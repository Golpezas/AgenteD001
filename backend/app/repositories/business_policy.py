"""
Repositorio de BusinessPolicy — CRUD con filtros específicos.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_policy import BusinessPolicy
from app.repositories.base import BaseRepository


class BusinessPolicyRepository(BaseRepository[BusinessPolicy]):
    """Repositorio para el modelo BusinessPolicy."""

    def __init__(self, session: AsyncSession):
        super().__init__(BusinessPolicy, session)

    async def get_by_type(self, policy_type: str) -> List[BusinessPolicy]:
        """
        Obtiene políticas filtrando por tipo.
        """
        stmt = (
            select(BusinessPolicy)
            .where(BusinessPolicy.policy_type == policy_type)
            .where(BusinessPolicy.is_active.is_(True))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active(self) -> List[BusinessPolicy]:
        """
        Obtiene políticas vigentes: effective_from <= hoy
        AND (effective_to IS NULL OR effective_to >= hoy).
        """
        today = date.today()
        stmt = (
            select(BusinessPolicy)
            .where(BusinessPolicy.is_active.is_(True))
            .where(
                (BusinessPolicy.effective_from.is_(None))
                | (BusinessPolicy.effective_from <= today)
            )
            .where(
                (BusinessPolicy.effective_to.is_(None))
                | (BusinessPolicy.effective_to >= today)
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
