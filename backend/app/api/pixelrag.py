"""
Endpoint PixelRAG — prueba de integración con renderizado y estado del pipeline.

Expone un endpoint de prueba para verificar que PixelRAGService está
disponible. En producción el endpoint NO está disponible (404).
Cuando el pipeline de análisis está registrado, la respuesta incluye
el bloque analysis_pipeline (R-X03).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.repositories.analysis import AnalysisJobRepository
from app.services.analysis.pipeline_state import pipeline_state

router = APIRouter(prefix="/api/v1/pixelrag", tags=["pixelrag"])


@router.get("/test")
async def pixelrag_test(db: AsyncSession = Depends(get_db)):
    """
    Endpoint de prueba para verificar disponibilidad de PixelRAG.

    Retorna el estado del servicio de renderizado y, cuando el pipeline
    de análisis está registrado, un bloque `analysis_pipeline` con
    active, last_successful_run y pending_jobs.
    """
    if settings.environment == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    try:
        from app.services.pixelrag import PixelRAGService

        service = PixelRAGService()
        status_info = await service.health()
        response = {
            "service": "pixelrag",
            **status_info,
        }

        # Bloque del pipeline de análisis solo cuando está registrado (R-X03)
        if pipeline_state.is_registered():
            snapshot = pipeline_state.snapshot()
            pending_jobs = await AnalysisJobRepository(db).count_by_status("pending")
            response["analysis_pipeline"] = {
                **snapshot,
                "pending_jobs": pending_jobs,
            }

        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PixelRAG error: {str(e)}",
        )
