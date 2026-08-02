"""
Analysis Orchestrator — coordina el pipeline multimodal
imagen/URL → preprocesamiento → Gemini Vision → JSON validado.
"""

import asyncio
import base64
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.models.analysis import AnalysisJob, AnalysisResult, AnalysisStatus
from app.repositories.analysis import (
    AnalysisJobRepository,
    AnalysisResultRepository,
    ScrapedSourceRepository,
)
from app.schemas.analysis import AnalysisProposal, ScreenshotResult
from app.services.analysis.gemini_client import GeminiClient
from app.services.analysis.pipeline_state import pipeline_state
from app.services.analysis.scraper import ScrapedContent, WebScraper
from app.services.notification import NotificationService
from app.services.pixelrag import PixelRAGService

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    Orquesta el pipeline completo de análisis:

    Imagen:
        1. Optimiza imagen con Pillow
        2. Envía a Gemini Vision
        3. Valida respuesta JSON con Pydantic

    URL:
        1. Scrapea HTML con httpx + BeautifulSoup
        2. Captura screenshot con PixelRAG
        3. Envía ambos a Gemini Vision
        4. Valida respuesta JSON con Pydantic

    Output: AnalysisResult con status="proposal" (NO auto-persistir)
    """

    def __init__(
        self,
        job_repo: AnalysisJobRepository,
        result_repo: AnalysisResultRepository,
        source_repo: ScrapedSourceRepository,
        gemini_client: GeminiClient,
        scraper: WebScraper,
        pixelrag: PixelRAGService,
        notification_service: NotificationService,
    ):
        self.job_repo = job_repo
        self.result_repo = result_repo
        self.source_repo = source_repo
        self.gemini = gemini_client
        self.scraper = scraper
        self.pixelrag = pixelrag
        self.notifications = notification_service

    async def process_job(self, job_id: str) -> Optional[AnalysisResult]:
        """
        Procesa un job de análisis completo.

        Args:
            job_id: UUID del AnalysisJob a procesar

        Returns:
            AnalysisResult creado con status="proposal", o None si error
        """
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found")
            return None

        try:
            # Marcar como procesando
            await self.job_repo.update(
                job.id,
                {
                    "status": AnalysisStatus.PROCESSING.value,
                    "started_at": datetime.utcnow(),
                },
            )

            if job.job_type == "image":
                proposal = await self._process_image(job)
            elif job.job_type == "url":
                proposal = await self._process_url(job)
            else:
                raise ValueError(f"Unknown job_type: {job.job_type}")

            # Crear resultado como propuesta (NO auto-persistir datos de negocio)
            result = await self.result_repo.create(
                {
                    "job_id": job.id,
                    "status": "proposal",
                    "product_name": proposal.product_name,
                    "extracted_price": proposal.extracted_price,
                    "confidence_score": proposal.confidence_score,
                    "raw_data": proposal.raw_data,
                    "proposal_data": proposal.model_dump(),
                }
            )

            # Marcar job completado
            await self.job_repo.update(
                job.id,
                {
                    "status": AnalysisStatus.COMPLETED.value,
                    "result_id": result.id,
                    "completed_at": datetime.utcnow(),
                },
            )

            # Notificar que hay propuesta pendiente
            await self.notifications.create_notification(
                type="system",
                category="analysis",
                title=f"Nueva propuesta de análisis: {proposal.product_name}",
                description=(
                    f"Se detectó '{proposal.product_name}' a "
                    f"{proposal.extracted_price:.2f} "
                    f"(confianza: {proposal.confidence_score:.0%})"
                ),
                severity="info",
                resource_type="analysis_result",
                resource_id=str(result.id),
            )

            # Registrar éxito del pipeline (R-X03)
            pipeline_state.mark_success()

            return result

        except Exception as e:
            logger.exception(f"Error processing job {job_id}: {e}")
            await self.job_repo.update(
                job.id,
                {
                    "status": AnalysisStatus.FAILED.value,
                    "error_message": str(e),
                    "completed_at": datetime.utcnow(),
                },
            )
            return None

    async def _process_image(self, job: AnalysisJob) -> AnalysisProposal:
        """Procesa análisis de imagen subida."""
        input_data = job.input_data if isinstance(job.input_data, dict) else {}
        image_bytes = input_data.get("image_bytes")
        if not image_bytes:
            raise ValueError("Image job requires image_bytes in input_data")
        # Soportar bytes directos o base64 str (desde la API)
        if isinstance(image_bytes, str):
            image_bytes = base64.b64decode(image_bytes)

        return await self.gemini.analyze_image(image_bytes)

    async def _process_url(self, job: AnalysisJob) -> AnalysisProposal:
        """Procesa análisis de URL: scrape + screenshot → Gemini."""
        input_data = job.input_data if isinstance(job.input_data, dict) else {}
        url = input_data.get("url")
        if not url:
            raise ValueError("URL job requires url in input_data")

        # Scrape HTML + metadata
        scraped = await self.scraper.scrape(url)

        # Captura screenshot con PixelRAG (ScreenshotResult completo)
        screenshot = None
        try:
            screenshot = await self.pixelrag.capture_for_analysis(url)
        except Exception as e:
            logger.warning(f"PixelRAG screenshot failed, continuing with text only: {e}")

        # Analizar con Gemini (HTML + screenshot)
        if screenshot:
            proposal = await self.gemini.analyze_scraped_content(
                html_content=scraped.text,
                screenshot=screenshot,
                prompt=self._build_url_prompt(scraped.text, scraped.metadata),
            )
        else:
            # Fallback: solo texto - usar analyze_image con prompt de texto
            proposal = await self.gemini.analyze_image(
                image_bytes=b"",
                prompt=self._build_text_prompt(scraped.text, scraped.metadata),
            )

        return proposal

    def _build_url_prompt(self, text: str, metadata: dict) -> str:
        """Construye prompt para análisis de URL con screenshot."""
        price_hints = []
        for key, value in metadata.items():
            if "price" in key.lower() or "og:price" in key:
                price_hints.append(f"{key}: {value}")

        price_context = "\n".join(price_hints) if price_hints else "No price metadata found"

        return (
            "Analyze this web page screenshot and extracted text to identify product information. "
            "Return a JSON object with exactly these fields: "
            "product_name (string), extracted_price (number), "
            "confidence_score (number between 0.0 and 1.0), "
            "currency (string, ISO 4217 code, default 'USD'), "
            "raw_data (object with any additional details). "
            "Only return valid JSON, no additional text.\n\n"
            f"Extracted Text (truncated):\n{text[:3000]}\n\n"
            f"Price Metadata:\n{price_context}"
        )

    def _build_text_prompt(self, text: str, metadata: dict) -> str:
        """Construye prompt para análisis solo texto (fallback sin screenshot)."""
        return (
            "Analyze this extracted web page text to identify product information. "
            "Return a JSON object with exactly these fields: "
            "product_name (string), extracted_price (number), "
            "confidence_score (number between 0.0 and 1.0), "
            "currency (string, ISO 4217 code, default 'USD'), "
            "raw_data (object with any additional details). "
            "Only return valid JSON, no additional text.\n\n"
            f"Text:\n{text[:5000]}"
        )

    async def approve_proposal(self, result_id: str) -> bool:
        """
        Aprueba una propuesta y aplica los cambios (upsert a Product/PriceList/etc).

        Args:
            result_id: UUID del AnalysisResult a aprobar

        Returns:
            True si se aprobó, False si no existe o no es proposal
        """
        result = await self.result_repo.get_by_id(result_id)
        if not result or result.status != "proposal":
            return False

        # Aquí iría la lógica de upsert a Product/PriceList/BusinessPolicy
        # Por ahora solo marcamos como accepted
        await self.result_repo.update(result.id, {"status": "accepted"})

        await self.notifications.create_notification(
            type="system",
            category="analysis",
            title=f"Propuesta aceptada: {result.product_name}",
            description=(
                f"La propuesta de '{result.product_name}' a "
                f"{result.extracted_price:.2f} "
                "ha sido aceptada y aplicada."
            ),
            severity="success",
            resource_type="analysis_result",
            resource_id=str(result.id),
        )

        return True

    async def reject_proposal(self, result_id: str, reason: str = "") -> bool:
        """
        Rechaza una propuesta.

        Args:
            result_id: UUID del AnalysisResult a rechazar
            reason: Motivo del rechazo

        Returns:
            True si se rechazó, False si no existe o no es proposal
        """
        result = await self.result_repo.get_by_id(result_id)
        if not result or result.status != "proposal":
            return False

        await self.result_repo.update(result.id, {"status": "rejected"})

        await self.notifications.create_notification(
            type="system",
            category="analysis",
            title=f"Propuesta rechazada: {result.product_name}",
            description=f"Motivo: {reason or 'Sin especificar'}",
            severity="warning",
            resource_type="analysis_result",
            resource_id=str(result.id),
        )

        return True

    async def get_job_status(self, job_id: str) -> Optional[dict]:
        """Obtiene estado actual de un job."""
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            return None

        result = await self.result_repo.get_by_job_id(job.id) if job.result_id else None

        return {
            "job_id": str(job.id),
            "status": job.status,
            "job_type": job.job_type,
            "error_message": job.error_message,
            "result": (
                {
                    "id": str(result.id),
                    "status": result.status,
                    "product_name": result.product_name,
                    "extracted_price": result.extracted_price,
                    "confidence_score": result.confidence_score,
                }
                if result
                else None
            ),
        }