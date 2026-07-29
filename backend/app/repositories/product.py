"""
Repositorio de Product — operaciones CRUD específicas.
"""

from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.base import BaseRepository
from app.models.price_list import PriceListItem


class ProductRepository(BaseRepository[Product]):
    """Repositorio para el modelo Product."""

    def __init__(self, session: AsyncSession):
        super().__init__(Product, session)

    async def get_with_prices(self, id: Any) -> Optional[Product]:
        """
        Obtiene un producto con sus ítems de precio asociados.
        """
        stmt = (
            select(Product)
            .where(Product.id == id)
            .where(Product.is_active.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
