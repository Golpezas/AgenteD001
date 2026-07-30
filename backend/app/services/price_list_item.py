"""
Servicio de PriceListItem — lógica de negocio para ítems de precio.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_list import PriceListItem
from app.repositories.price_list_item import PriceListItemRepository
from app.services.base import BaseService


class PriceListItemService(BaseService[PriceListItem]):
    """Servicio para operaciones con ítems de listas de precios."""

    def __init__(self, session: AsyncSession):
        repository = PriceListItemRepository(session)
        super().__init__(repository)
