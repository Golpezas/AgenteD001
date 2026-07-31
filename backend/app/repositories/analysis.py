"""
Repositorios para el módulo de análisis de imágenes y URLs.

Define repositorios async SQLAlchemy para AnalysisJob,
AnalysisResult y ScrapedSource con filtros especializados.
"""

from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisJob, AnalysisResult, ScrapedSource
from app.repositories.base import BaseRepository


class AnalysisJobRepository(BaseRepository[AnalysisJob]):
    """Repositorio para el modelo AnalysisJob."""

    def __init__(self, session: AsyncSession):
        super().__init__(AnalysisJob, session)

    async def count_by_status(self, status: str) -> int:
        """Cuenta jobs activos en un estado dado (R-X03)."""
        stmt = (
            select(func.count())
            .select_from(AnalysisJob)
            .where(
                AnalysisJob.status == status,
                AnalysisJob.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0


class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    """Repositorio para el modelo AnalysisResult."""

    def __init__(self, session: AsyncSession):
        super().__init__(AnalysisResult, session)

    async def get_by_job_id(self, job_id: Any) -> Optional[AnalysisResult]:
        """Obtiene el resultado de análisis asociado a un job."""
        stmt = select(AnalysisResult).where(AnalysisResult.job_id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class ScrapedSourceRepository(BaseRepository[ScrapedSource]):
    """Repositorio para el modelo ScrapedSource."""

    def __init__(self, session: AsyncSession):
        super().__init__(ScrapedSource, session)

    async def get_by_url(self, url: str) -> Optional[ScrapedSource]:
        """Obtiene una fuente por su URL."""
        stmt = select(ScrapedSource).where(ScrapedSource.url == url)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
