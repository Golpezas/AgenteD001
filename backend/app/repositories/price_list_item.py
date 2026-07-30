"""
Repositorio de PriceListItem — operaciones CRUD.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_list import PriceListItem
from app.repositories.base import BaseRepository


class PriceListItemRepository(BaseRepository[PriceListItem]):
    """Repositorio para el modelo PriceListItem."""

    def __init__(self, session: AsyncSession):
        super().__init__(PriceListItem, session)
