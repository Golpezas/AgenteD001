"""
Tests para AnalysisRepository, AnalysisResultRepository, ScrapedSourceRepository.

RED phase: estos tests referencian código que aún no existe,
por lo tanto fallarán con ModuleNotFoundError hasta que se
implementen los repositorios (GREEN phase).
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisJob, AnalysisResult, ScrapedSource
from app.repositories.analysis import (
    AnalysisJobRepository,
    AnalysisResultRepository,
    ScrapedSourceRepository,
)


class TestAnalysisJobRepository:
    """Suite de tests para AnalysisJobRepository."""

    @pytest.mark.asyncio
    async def test_create_job(self, db_session: AsyncSession):
        """Debe crear un job de análisis."""
        repo = AnalysisJobRepository(db_session)
        job = await repo.create(
            {
                "job_type": "image",
                "input_data": {"image_url": "https://example.com/photo.jpg"},
            }
        )
        assert job.id is not None
        assert job.job_type == "image"
        assert job.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Debe obtener un job por su ID."""
        repo = AnalysisJobRepository(db_session)
        created = await repo.create(
            {
                "job_type": "url",
                "input_data": {"url": "https://example.com"},
            }
        )
        found = await repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Debe retornar None si el job no existe."""
        repo = AnalysisJobRepository(db_session)
        found = await repo.get_by_id(uuid.uuid4())
        assert found is None

    @pytest.mark.asyncio
    async def test_get_all_paginated(self, db_session: AsyncSession):
        """Debe retornar jobs paginados."""
        repo = AnalysisJobRepository(db_session)
        for i in range(5):
            await repo.create(
                {
                    "job_type": "image",
                    "input_data": {"image_url": f"https://example.com/{i}.jpg"},
                }
            )
        result = await repo.get_all(page=1, per_page=3)
        assert len(result["items"]) == 3
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["per_page"] == 3

    @pytest.mark.asyncio
    async def test_filter_by_status(self, db_session: AsyncSession):
        """Debe filtrar jobs por estado."""
        repo = AnalysisJobRepository(db_session)
        await repo.create(
            {"job_type": "image", "input_data": {}, "status": "pending"}
        )
        await repo.create(
            {"job_type": "url", "input_data": {}, "status": "processing"}
        )
        await repo.create(
            {"job_type": "image", "input_data": {}, "status": "pending"}
        )

        result = await repo.get_all(
            page=1,
            per_page=10,
            filters={"status": "pending"},
        )
        assert len(result["items"]) == 2
        assert all(j.status == "pending" for j in result["items"])

    @pytest.mark.asyncio
    async def test_filter_by_job_type(self, db_session: AsyncSession):
        """Debe filtrar jobs por tipo."""
        repo = AnalysisJobRepository(db_session)
        await repo.create(
            {"job_type": "image", "input_data": {}}
        )
        await repo.create(
            {"job_type": "url", "input_data": {}}
        )
        await repo.create(
            {"job_type": "image", "input_data": {}}
        )

        result = await repo.get_all(
            page=1,
            per_page=10,
            filters={"job_type": "image"},
        )
        assert len(result["items"]) == 2
        assert all(j.job_type == "image" for j in result["items"])

    @pytest.mark.asyncio
    async def test_update_status(self, db_session: AsyncSession):
        """Debe actualizar el estado del job."""
        repo = AnalysisJobRepository(db_session)
        job = await repo.create(
            {"job_type": "image", "input_data": {}}
        )
        updated = await repo.update(job.id, {"status": "completed"})
        assert updated is not None
        assert updated.status == "completed"

    @pytest.mark.asyncio
    async def test_soft_delete(self, db_session: AsyncSession):
        """Debe soportar soft delete."""
        repo = AnalysisJobRepository(db_session)
        job = await repo.create(
            {"job_type": "image", "input_data": {}}
        )
        assert job.is_active is True
        deleted = await repo.soft_delete(job.id)
        assert deleted is not None
        assert deleted.is_active is False

    @pytest.mark.asyncio
    async def test_count_by_status(self, db_session: AsyncSession):
        """Debe contar jobs activos por estado."""
        repo = AnalysisJobRepository(db_session)
        await repo.create(
            {"job_type": "image", "input_data": {}, "status": "pending"}
        )
        await repo.create(
            {"job_type": "url", "input_data": {}, "status": "processing"}
        )
        await repo.create(
            {"job_type": "image", "input_data": {}, "status": "pending"}
        )

        count = await repo.count_by_status("pending")
        assert count == 2

    @pytest.mark.asyncio
    async def test_count_by_status_excludes_inactive(self, db_session: AsyncSession):
        """Debe excluir jobs soft-deleted del conteo."""
        repo = AnalysisJobRepository(db_session)
        job = await repo.create(
            {"job_type": "image", "input_data": {}, "status": "pending"}
        )
        await repo.soft_delete(job.id)

        count = await repo.count_by_status("pending")
        assert count == 0


class TestAnalysisResultRepository:
    """Suite de tests para AnalysisResultRepository."""

    @pytest.mark.asyncio
    async def test_create_result(self, db_session: AsyncSession):
        """Debe crear un resultado de análisis."""
        job_repo = AnalysisJobRepository(db_session)
        job = await job_repo.create(
            {"job_type": "image", "input_data": {"image_url": "https://example.com/img.jpg"}}
        )

        repo = AnalysisResultRepository(db_session)
        result = await repo.create(
            {
                "job_id": job.id,
                "status": "proposal",
                "product_name": "Test Product",
                "extracted_price": 99.99,
                "confidence_score": 0.85,
            }
        )
        assert result.id is not None
        assert result.job_id == job.id
        assert result.status == "proposal"
        assert result.product_name == "Test Product"

    @pytest.mark.asyncio
    async def test_get_by_job_id(self, db_session: AsyncSession):
        """Debe buscar resultado por job_id."""
        job_repo = AnalysisJobRepository(db_session)
        job = await job_repo.create(
            {"job_type": "url", "input_data": {"url": "https://example.com"}}
        )

        repo = AnalysisResultRepository(db_session)
        created = await repo.create(
            {
                "job_id": job.id,
                "status": "proposal",
                "product_name": "Job Result",
            }
        )

        found = await repo.get_by_job_id(job.id)
        assert found is not None
        assert found.job_id == job.id

    @pytest.mark.asyncio
    async def test_get_by_job_id_not_found(self, db_session: AsyncSession):
        """Debe retornar None si no hay resultado para ese job."""
        repo = AnalysisResultRepository(db_session)
        found = await repo.get_by_job_id(uuid.uuid4())
        assert found is None

    @pytest.mark.asyncio
    async def test_filter_by_status(self, db_session: AsyncSession):
        """Debe filtrar resultados por estado."""
        job_repo = AnalysisJobRepository(db_session)
        job = await job_repo.create(
            {"job_type": "image", "input_data": {}}
        )

        repo = AnalysisResultRepository(db_session)
        await repo.create({"job_id": job.id, "status": "proposal"})
        await repo.create({"job_id": job.id, "status": "accepted"})
        await repo.create({"job_id": job.id, "status": "proposal"})

        result = await repo.get_all(
            page=1,
            per_page=10,
            filters={"status": "proposal"},
        )
        assert len(result["items"]) == 2
        assert all(r.status == "proposal" for r in result["items"])


class TestScrapedSourceRepository:
    """Suite de tests para ScrapedSourceRepository."""

    @pytest.mark.asyncio
    async def test_create_source(self, db_session: AsyncSession):
        """Debe crear una fuente de scraping."""
        repo = ScrapedSourceRepository(db_session)
        source = await repo.create(
            {
                "url": "https://competidor.com/products",
                "name": "Competidor Principal",
                "schedule_interval_minutes": 60,
            }
        )
        assert source.id is not None
        assert source.url == "https://competidor.com/products"
        assert source.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_url(self, db_session: AsyncSession):
        """Debe buscar una fuente por URL."""
        repo = ScrapedSourceRepository(db_session)
        created = await repo.create(
            {
                "url": "https://example-source.com",
                "name": "Test Source",
            }
        )
        found = await repo.get_by_url("https://example-source.com")
        assert found is not None
        assert found.url == created.url

    @pytest.mark.asyncio
    async def test_get_by_url_not_found(self, db_session: AsyncSession):
        """Debe retornar None si la URL no existe."""
        repo = ScrapedSourceRepository(db_session)
        found = await repo.get_by_url("https://nonexistent.com")
        assert found is None

    @pytest.mark.asyncio
    async def test_get_active_sources(self, db_session: AsyncSession):
        """Debe filtrar solo fuentes activas."""
        repo = ScrapedSourceRepository(db_session)
        await repo.create(
            {
                "url": "https://active.com",
                "name": "Active Source",
                "schedule_interval_minutes": 60,
            }
        )
        await repo.create(
            {
                "url": "https://inactive.com",
                "name": "Inactive Source",
                "schedule_interval_minutes": 60,
            }
        )
        # Desactivar la segunda fuente
        sources = await repo.get_all(page=1, per_page=10)
        inactive = sources["items"][1]
        await repo.soft_delete(inactive.id)

        result = await repo.get_all(page=1, per_page=10)
        assert all(s.is_active for s in result["items"])

    @pytest.mark.asyncio
    async def test_update_schedule(self, db_session: AsyncSession):
        """Debe actualizar el intervalo de monitoreo."""
        repo = ScrapedSourceRepository(db_session)
        source = await repo.create(
            {
                "url": "https://schedulable.com",
                "name": "Schedulable",
                "schedule_interval_minutes": 30,
            }
        )
        updated = await repo.update(
            source.id, {"schedule_interval_minutes": 120}
        )
        assert updated is not None
        assert updated.schedule_interval_minutes == 120
