"""
Schemas para PriceList — creación y respuesta.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PriceListCreate(BaseModel):
    """Schema para crear una lista de precios."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class PriceListUpdate(BaseModel):
    """Schema para actualizar una lista de precios."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class PriceListResponse(BaseModel):
    """Schema de respuesta para PriceList."""

    id: UUID
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
