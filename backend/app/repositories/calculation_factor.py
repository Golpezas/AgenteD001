"""
Repositorio de CalculationFactor — CRUD con filtros específicos.
"""

from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calculation_factor import CalculationFactor
from app.repositories.base import BaseRepository


class CalculationFactorRepository(BaseRepository[CalculationFactor]):
    """Repositorio para el modelo CalculationFactor."""

    def __init__(self, session: AsyncSession):
        super().__init__(CalculationFactor, session)

    async def get_by_concept_and_tier(
        self,
        concept_key: str,
        technology_tier: str,
    ) -> Optional[CalculationFactor]:
        """
        Obtiene un factor por tupla (concept_key, technology_tier).
        """
        stmt = (
            select(CalculationFactor)
            .where(CalculationFactor.concept_key == concept_key)
            .where(CalculationFactor.technology_tier == technology_tier)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[Any] = None,
        include_unavailable: bool = False,
    ) -> Dict[str, Any]:
        """
        Obtiene factores paginados.

        Por defecto excluye factores con is_available=False.
        Usar include_unavailable=True para incluirlos.
        """
        if filters is None:
            filters = {}

        # Filtro de disponibilidad
        if not include_unavailable:
            filters["is_available"] = True

        return await super().get_all(
            page=page,
            per_page=per_page,
            filters=filters,
            order_by=order_by,
        )
