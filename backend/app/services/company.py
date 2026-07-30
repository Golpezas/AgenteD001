"""
Servicio de Company — lógica de negocio para empresas.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.repositories.company import CompanyRepository
from app.services.base import BaseService
from app.services.notification import NotificationService

logger = logging.getLogger("uvicorn")


class CompanyService(BaseService[Company]):
    """Servicio para operaciones de negocio con empresas."""

    def __init__(self, session: AsyncSession):
        self.session = session
        repository = CompanyRepository(session)
        super().__init__(repository)

    async def create(self, data: Dict[str, Any]) -> Company:
        instance = await super().create(data)
        try:
            notif_service = NotificationService(self.session)
            await notif_service.create_notification(
                type="system",
                category="company",
                title=f"Cliente registrado: {instance.business_name}",
                severity="success",
                resource_type="company",
                resource_id=str(instance.id),
            )
        except Exception as e:
            logger.error(f"Error creando notificación para cliente: {e}")
        return instance

    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[Company]:
        instance = await super().update(id, data)
        if instance:
            try:
                notif_service = NotificationService(self.session)
                await notif_service.create_notification(
                    type="system",
                    category="company",
                    title=f"Cliente actualizado: {instance.business_name}",
                    severity="info",
                    resource_type="company",
                    resource_id=str(instance.id),
                )
            except Exception as e:
                logger.error(f"Error creando notificación para cliente: {e}")
        return instance

    async def deactivate(self, id: Any) -> Optional[Company]:
        instance = await super().deactivate(id)
        if instance:
            try:
                notif_service = NotificationService(self.session)
                await notif_service.create_notification(
                    type="system",
                    category="company",
                    title=f"Cliente eliminado: {instance.business_name}",
                    severity="warning",
                    resource_type="company",
                    resource_id=str(instance.id),
                )
            except Exception as e:
                logger.error(f"Error creando notificación para cliente: {e}")
        return instance

    async def get_with_deals(self, company_id: Any) -> Optional[Company]:
        """
        Obtiene una empresa con información adicional.
        Placeholder para futura integración con deals.
        """
        return await self.get_by_id(company_id)
