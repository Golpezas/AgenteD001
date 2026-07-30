"""
Servicio de BusinessPolicy — lógica de negocio para políticas comerciales.

Opera sobre el repositorio BusinessPolicyRepository para consultar
políticas de descuento, beneficio, financiamiento y reglas generales.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_policy import BusinessPolicy
from app.repositories.business_policy import BusinessPolicyRepository
from app.services.base import BaseService


class BusinessPolicyService(BaseService[BusinessPolicy]):
    """Servicio para operaciones de negocio con políticas comerciales."""

    def __init__(self, session: AsyncSession):
        repository = BusinessPolicyRepository(session)
        super().__init__(repository)

    async def get_by_type(
        self,
        policy_type: str,
        page: int = 1,
        per_page: int = 10,
    ) -> dict:
        """Obtiene políticas activas filtradas por tipo, con paginación.

        Args:
            policy_type: Tipo de política (discount, benefit, financing, policy).
            page: Número de página.
            per_page: Ítems por página.

        Returns:
            Dict con items, total, page, per_page.
        """
        return await self.repository.get_all(
            page=page,
            per_page=per_page,
            filters={"policy_type": policy_type},
        )

    async def get_active(
        self,
        page: int = 1,
        per_page: int = 10,
    ) -> dict:
        """Obtiene políticas vigentes paginadas.

        Aplica el filtro de vigencia por fechas (effective_from/effective_to)
        y retorna solo políticas con is_active=True.

        Args:
            page: Número de página.
            per_page: Ítems por página.

        Returns:
            Dict con items, total, page, per_page.
        """
        all_active = await self.repository.get_active()
        total = len(all_active)

        start = (page - 1) * per_page
        end = start + per_page
        items = all_active[start:end]

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
        }
