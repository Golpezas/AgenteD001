"""
Tests para los modelos AnalysisJob, AnalysisResult, ScrapedSource.

RED phase: estos tests referencian código que aún no existe,
por lo tanto fallarán con ModuleNotFoundError hasta que se
implementen los modelos (GREEN phase).
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.analysis import AnalysisJob, AnalysisResult, ScrapedSource


class TestAnalysisJobModel:
    """Suite de tests para el modelo AnalysisJob."""

    @pytest.mark.asyncio
    async def test_create_image_job(self, db_session: AsyncSession):
        """Debe crear un job de análisis de imagen con campos obligatorios."""
        job = AnalysisJob(
            job_type="image",
            input_data={"image_url": "https://example.com/photo.jpg"},
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        assert job.id is not None
        assert isinstance(job.id, uuid.UUID)
        assert job.job_type == "image"
        assert job.input_data == {"image_url": "https://example.com/photo.jpg"}
        assert job.status == "pending"
        assert job.result_id is None
        assert job.error_message is None
        assert job.is_active is True
        assert isinstance(job.created_at, datetime)
        assert isinstance(job.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_create_url_job(self, db_session: AsyncSession):
        """Debe crear un job de análisis de URL."""
        job = AnalysisJob(
            job_type="url",
            input_data={"url": "https://competidor.com/producto"},
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        assert job.job_type == "url"
        assert job.input_data == {"url": "https://competidor.com/producto"}

    @pytest.mark.asyncio
    async def test_update_job_status(self, db_session: AsyncSession):
        """Debe actualizar el estado del job."""
        job = AnalysisJob(job_type="image", input_data={"image_url": "https://example.com/img.png"})
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        job.status = "processing"
        await db_session.commit()
        await db_session.refresh(job)

        assert job.status == "processing"

    @pytest.mark.asyncio
    async def test_job_error_message(self, db_session: AsyncSession):
        """Debe almacenar un mensaje de error cuando el job falla."""
        job = AnalysisJob(
            job_type="url",
            input_data={"url": "https://invalid.url"},
            status="failed",
            error_message="Timeout after 30s",
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        assert job.status == "failed"
        assert job.error_message == "Timeout after 30s"


class TestAnalysisResultModel:
    """Suite de tests para el modelo AnalysisResult."""

    @pytest.mark.asyncio
    async def test_create_result_with_proposal(self, db_session: AsyncSession):
        """Debe crear un resultado con propuesta de producto."""
        job = AnalysisJob(job_type="image", input_data={"image_url": "https://example.com/img.jpg"})
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        result = AnalysisResult(
            job_id=job.id,
            status="proposal",
            product_name="Balcony Plan Premium",
            extracted_price=299.99,
            currency="ARS",
            confidence_score=0.85,
            proposal_data={"source": "gemini_vision", "fields_extracted": 5},
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        assert result.id is not None
        assert result.job_id == job.id
        assert result.status == "proposal"
        assert result.product_name == "Balcony Plan Premium"
        assert float(result.extracted_price) == 299.99
        assert result.currency == "ARS"
        assert result.confidence_score == 0.85
        assert result.proposal_data is not None

    @pytest.mark.asyncio
    async def test_result_accepted_status(self, db_session: AsyncSession):
        """Debe permitir marcar un resultado como aceptado."""
        job = AnalysisJob(job_type="url", input_data={"url": "https://example.com"})
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        result = AnalysisResult(
            job_id=job.id,
            status="accepted",
            product_name="Test Product",
            extracted_price=100.0,
            confidence_score=0.92,
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        assert result.status == "accepted"

    @pytest.mark.asyncio
    async def test_result_rejected_status(self, db_session: AsyncSession):
        """Debe permitir marcar un resultado como rechazado."""
        job = AnalysisJob(job_type="url", input_data={"url": "https://example.com"})
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        result = AnalysisResult(
            job_id=job.id,
            status="rejected",
            product_name="Bad Product",
            extracted_price=50.0,
            confidence_score=0.3,
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        assert result.status == "rejected"


class TestScrapedSourceModel:
    """Suite de tests para el modelo ScrapedSource."""

    @pytest.mark.asyncio
    async def test_create_scraped_source(self, db_session: AsyncSession):
        """Debe crear una fuente de scraping con URL."""
        source = ScrapedSource(
            url="https://competidor.com/products",
            name="Competidor Principal",
            schedule_interval_minutes=60,
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        assert source.id is not None
        assert isinstance(source.id, uuid.UUID)
        assert source.url == "https://competidor.com/products"
        assert source.name == "Competidor Principal"
        assert source.schedule_interval_minutes == 60
        assert source.is_active is True
        assert source.last_analyzed_at is None

    @pytest.mark.asyncio
    async def test_scraped_source_deactivate(self, db_session: AsyncSession):
        """Debe permitir desactivar una fuente (soft delete)."""
        source = ScrapedSource(url="https://example.com", name="Test Source")
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        source.is_active = False
        await db_session.commit()
        await db_session.refresh(source)

        assert source.is_active is False

    @pytest.mark.asyncio
    async def test_scraped_source_unique_url(self, db_session: AsyncSession):
        """Las URLs de fuentes deben ser únicas."""
        source1 = ScrapedSource(url="https://unique.com", name="Source 1")
        db_session.add(source1)
        await db_session.commit()

        source2 = ScrapedSource(url="https://unique.com", name="Source 2")
        db_session.add(source2)
        with pytest.raises(Exception):
            await db_session.commit()
        await db_session.rollback()
