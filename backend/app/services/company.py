"""
Servicio de Company — lógica de negocio para empresas.
"""

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.repositories.company import CompanyRepository
from app.services.base import BaseService


class CompanyService(BaseService[Company]):
    """Servicio para operaciones de negocio con empresas."""

    def __init__(self, session: AsyncSession):
        repository = CompanyRepository(session)
        super().__init__(repository)

    async def get_with_deals(self, company_id: Any) -> Optional[Company]:
        """
        Obtiene una empresa con información adicional.
        Placeholder para futura integración con deals.
        """
        return await self.get_by_id(company_id)
