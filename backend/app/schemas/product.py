"""
Schemas para Product — creación, actualización y respuesta.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """Campos base compartidos."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    family: Optional[Literal["Zeus", "Balcony", "MasPedidos", "Prescriptor", "Pidea", "CASH", "Servicios Globales", "Otros"]] = None
    category: Optional[Literal["software", "hardware", "servicio", "suscripcion", "consultoria", "capacitacion", "marketplace"]] = None
    extra_data: Optional[dict] = None
    company_id: Optional[UUID] = None


class ProductCreate(ProductBase):
    """Schema para crear un producto."""

    pass


class ProductUpdate(BaseModel):
    """Schema para actualizar un producto (todos los campos opcionales)."""

    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    family: Optional[Literal["Zeus", "Balcony", "MasPedidos", "Prescriptor", "Pidea", "CASH", "Servicios Globales", "Otros"]] = None
    category: Optional[Literal["software", "hardware", "servicio", "suscripcion", "consultoria", "capacitacion", "marketplace"]] = None
    extra_data: Optional[dict] = None
    company_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema de respuesta para Product."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductList(BaseModel):
    """Lista paginada de productos."""

    items: list[ProductResponse]
    total: int
    page: int
    per_page: int

    model_config = {"from_attributes": True}
