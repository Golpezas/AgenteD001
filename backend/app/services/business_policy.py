"""
Servicio de BusinessPolicy — lógica de negocio para políticas comerciales.

Opera sobre el repositorio BusinessPolicyRepository para consultar
políticas de descuento, beneficio, financiamiento y reglas generales.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_policy import BusinessPolicy
from app.repositories.business_policy import BusinessPolicyRepository
from app.services.base import BaseService
from app.services.notification import NotificationService

logger = logging.getLogger("uvicorn")


class BusinessPolicyService(BaseService[BusinessPolicy]):
    """Servicio para operaciones de negocio con políticas comerciales."""

    def __init__(self, session: AsyncSession):
        self.session = session
        repository = BusinessPolicyRepository(session)
        super().__init__(repository)

    async def create(self, data: Dict[str, Any]) -> BusinessPolicy:
        instance = await super().create(data)
        try:
            notif_service = NotificationService(self.session)
            await notif_service.create_notification(
                type="system",
                category="policy",
                title=f"Política creada: {instance.name}",
                severity="success",
                resource_type="business_policy",
                resource_id=str(instance.id),
            )
        except Exception as e:
            logger.error(f"Error creando notificación para política: {e}")
        return instance

    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[BusinessPolicy]:
        instance = await super().update(id, data)
        if instance:
            try:
                notif_service = NotificationService(self.session)
                await notif_service.create_notification(
                    type="system",
                    category="policy",
                    title=f"Política actualizada: {instance.name}",
                    severity="info",
                    resource_type="business_policy",
                    resource_id=str(instance.id),
                )
            except Exception as e:
                logger.error(f"Error creando notificación para política: {e}")
        return instance

    async def deactivate(self, id: Any) -> Optional[BusinessPolicy]:
        instance = await super().deactivate(id)
        if instance:
            try:
                notif_service = NotificationService(self.session)
                await notif_service.create_notification(
                    type="system",
                    category="policy",
                    title=f"Política eliminada: {instance.name}",
                    severity="warning",
                    resource_type="business_policy",
                    resource_id=str(instance.id),
                )
            except Exception as e:
                logger.error(f"Error creando notificación para política: {e}")
        return instance

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
