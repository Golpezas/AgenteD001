"""
Servicio de CalculationFactor — lógica de negocio para factores de licenciamiento.

Opera sobre el repositorio CalculationFactorRepository para consultar
factores multiplicadores por concepto y technology tier.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calculation_factor import CalculationFactor
from app.repositories.calculation_factor import CalculationFactorRepository
from app.services.base import BaseService


class CalculationFactorService(BaseService[CalculationFactor]):
    """Servicio para operaciones de negocio con factores de licenciamiento."""

    def __init__(self, session: AsyncSession):
        repository = CalculationFactorRepository(session)
        super().__init__(repository)

    async def get_by_concept_and_tier(
        self,
        concept_key: str,
        technology_tier: str,
    ) -> Optional[CalculationFactor]:
        """Obtiene un factor por tupla (concept_key, technology_tier).

        Args:
            concept_key: Clave del concepto (ej: accesos_simultaneos).
            technology_tier: Tier (Express, Advanced, Premium).

        Returns:
            El factor encontrado o None si no existe.
        """
        return await self.repository.get_by_concept_and_tier(
            concept_key=concept_key,
            technology_tier=technology_tier,
        )

    async def get_all(
        self,
        page: int = 1,
        per_page: int = 10,
        technology_tier: Optional[str] = None,
        include_unavailable: bool = False,
        filters: Optional[dict] = None,
    ) -> dict:
        """Obtiene factores paginados con filtros de negocio.

        Args:
            page: Número de página.
            per_page: Ítems por página.
            technology_tier: Filtrar por tier (Express, Advanced, Premium).
            include_unavailable: Incluir factores con is_available=False.
            filters: Filtros adicionales (sobrescribe technology_tier si hay conflicto).

        Returns:
            Dict con items, total, page, per_page.
        """
        if filters is None:
            filters = {}
        if technology_tier:
            filters["technology_tier"] = technology_tier

        return await self.repository.get_all(
            page=page,
            per_page=per_page,
            filters=filters or None,
            include_unavailable=include_unavailable,
        )
