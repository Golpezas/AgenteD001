"""
Servicio de PriceListItem — lógica de negocio para ítems de precio.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_list import PriceListItem
from app.repositories.price_list_item import PriceListItemRepository
from app.services.base import BaseService
from app.services.notification import NotificationService

logger = logging.getLogger("uvicorn")


class PriceListItemService(BaseService[PriceListItem]):
    """Servicio para operaciones con ítems de listas de precios."""

    def __init__(self, session: AsyncSession):
        self.session = session
        repository = PriceListItemRepository(session)
        super().__init__(repository)

    async def create(self, data: Dict[str, Any]) -> PriceListItem:
        instance = await super().create(data)
        try:
            product_name = instance.product.name
            notif_service = NotificationService(self.session)
            await notif_service.create_notification(
                type="system",
                category="price",
                title=f"Precio asignado: {product_name}",
                severity="success",
                resource_type="price_list_item",
                resource_id=str(instance.id),
            )
        except Exception as e:
            logger.error(f"Error creando notificación para precio: {e}")
        return instance

    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[PriceListItem]:
        instance = await super().update(id, data)
        if instance:
            try:
                product_name = instance.product.name
                notif_service = NotificationService(self.session)
                await notif_service.create_notification(
                    type="system",
                    category="price",
                    title=f"Precio actualizado: {product_name}",
                    severity="info",
                    resource_type="price_list_item",
                    resource_id=str(instance.id),
                )
            except Exception as e:
                logger.error(f"Error creando notificación para precio: {e}")
        return instance

    async def deactivate(self, id: Any) -> Optional[PriceListItem]:
        instance = await super().deactivate(id)
        if instance:
            try:
                notif_service = NotificationService(self.session)
                await notif_service.create_notification(
                    type="system",
                    category="price",
                    title="Precio eliminado",
                    severity="warning",
                    resource_type="price_list_item",
                    resource_id=str(instance.id),
                )
            except Exception as e:
                logger.error(f"Error creando notificación para precio: {e}")
        return instance
