"""
Servicio de Product — lógica de negocio para productos.
"""

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.product import ProductRepository
from app.services.base import BaseService


class ProductService(BaseService[Product]):
    """Servicio para operaciones de negocio con productos."""

    def __init__(self, session: AsyncSession):
        repository = ProductRepository(session)
        super().__init__(repository)

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
