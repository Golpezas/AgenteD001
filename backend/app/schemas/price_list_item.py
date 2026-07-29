"""
Schemas para PriceListItem — creación y respuesta.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PriceListItemCreate(BaseModel):
    """Schema para crear un ítem en una lista de precios."""

    product_id: UUID
    price_list_id: UUID
    price: float = Field(..., gt=0)
    currency: str = Field(default="ARS", max_length=3)
    effective_from: date
    effective_to: Optional[date] = None
    extra_data: Optional[dict] = None


class PriceListItemUpdate(BaseModel):
    """Schema para actualizar un ítem de precio."""

    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    extra_data: Optional[dict] = None
    is_active: Optional[bool] = None


class PriceListItemResponse(BaseModel):
    """Schema de respuesta para PriceListItem."""

    id: UUID
    product_id: UUID
    price_list_id: UUID
    price: float
    currency: str
    effective_from: date
    effective_to: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    extra_data: Optional[dict]

    model_config = {"from_attributes": True}
