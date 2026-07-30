"""
Endpoint de PriceListItems — CRUD /api/v1/price-list-items.

Lista y actualiza ítems dentro de listas de precios.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.price_list_item import (
    PriceListItemCreate,
    PriceListItemResponse,
    PriceListItemUpdate,
)
from app.services.price_list_item import PriceListItemService

router = APIRouter(prefix="/api/v1/price-list-items", tags=["price-list-items"])


@router.get("", response_model=PaginatedResponse[PriceListItemResponse])
async def list_price_list_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lista ítems de listas de precios con paginación."""
    service = PriceListItemService(db)
    return await service.get_all(page=page, per_page=per_page)


@router.get("/{item_id}", response_model=PriceListItemResponse)
async def get_price_list_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Obtiene un ítem de precio por ID."""
    service = PriceListItemService(db)
    item = await service.get_by_id(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.post("", response_model=PriceListItemResponse, status_code=status.HTTP_201_CREATED)
async def create_price_list_item(
    payload: PriceListItemCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea un nuevo ítem en una lista de precios."""
    service = PriceListItemService(db)
    return await service.create(payload.model_dump())


@router.put("/{item_id}", response_model=PriceListItemResponse)
async def update_price_list_item(
    item_id: UUID,
    payload: PriceListItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza un ítem de precio (precio, moneda, fechas)."""
    service = PriceListItemService(db)
    item = await service.update(item_id, payload.model_dump(exclude_unset=True))
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.delete("/{item_id}", response_model=PriceListItemResponse)
async def delete_price_list_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Elimina (soft delete) un ítem de precio."""
    service = PriceListItemService(db)
    item = await service.deactivate(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item
