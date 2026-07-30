"""
Servicio de Product — lógica de negocio para productos.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.product import ProductRepository
from app.services.base import BaseService
from app.services.notification import NotificationService

logger = logging.getLogger("uvicorn")


class ProductService(BaseService[Product]):
    """Servicio para operaciones de negocio con productos."""

    def __init__(self, session: AsyncSession):
        self.session = session
        repository = ProductRepository(session)
        super().__init__(repository)

    async def create(self, data: Dict[str, Any]) -> Product:
        instance = await super().create(data)
        try:
            notif_service = NotificationService(self.session)
            await notif_service.create_notification(
                type="system",
                category="product",
                title=f"Producto creado: {instance.name}",
                severity="success",
                resource_type="product",
                resource_id=str(instance.id),
            )
        except Exception as e:
            logger.error(f"Error creando notificación para producto: {e}")
        return instance

    async def update(self, id: Any, data: Dict[str, Any]) -> Optional[Product]:
        instance = await super().update(id, data)
        if instance:
            try:
                notif_service = NotificationService(self.session)
                await notif_service.create_notification(
                    type="system",
                    category="product",
                    title=f"Producto actualizado: {instance.name}",
                    severity="info",
                    resource_type="product",
                    resource_id=str(instance.id),
                )
            except Exception as e:
                logger.error(f"Error creando notificación para producto: {e}")
        return instance

    async def deactivate(self, id: Any) -> Optional[Product]:
        instance = await super().deactivate(id)
        if instance:
            try:
                notif_service = NotificationService(self.session)
                await notif_service.create_notification(
                    type="system",
                    category="product",
                    title=f"Producto eliminado: {instance.name}",
                    severity="warning",
                    resource_type="product",
                    resource_id=str(instance.id),
                )
            except Exception as e:
                logger.error(f"Error creando notificación para producto: {e}")
        return instance

    async def get_by_family(
        self,
        family: str,
        page: int = 1,
        per_page: int = 10,
    ) -> Dict[str, Any]:
        """Obtiene productos filtrados por familia."""
        return await self.repository.get_all(
            page=page,
            per_page=per_page,
            filters={"family": family},
        )

    async def get_with_prices(self, product_id: Any) -> Optional[Product]:
        """Obtiene un producto con sus precios asociados."""
        return await self.repository.get_with_prices(product_id)
