"""
Schemas para Company — creación, actualización y respuesta.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    """Campos base compartidos por todos los schemas de Company."""

    business_name: str = Field(..., min_length=1, max_length=255)
    cuit: Optional[str] = Field(None, max_length=20)
    legal_rep: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    fiscal_address: Optional[str] = None
    vertical: Optional[str] = Field(None, max_length=100)
    tech_tier: Optional[str] = Field(None, max_length=50)
    extra_data: Optional[dict] = None


class CompanyCreate(CompanyBase):
    """Schema para crear una empresa."""

    pass


class CompanyUpdate(BaseModel):
    """Schema para actualizar una empresa (todos los campos opcionales)."""

    business_name: Optional[str] = Field(None, min_length=1, max_length=255)
    cuit: Optional[str] = Field(None, max_length=20)
    legal_rep: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    fiscal_address: Optional[str] = None
    vertical: Optional[str] = Field(None, max_length=100)
    tech_tier: Optional[str] = Field(None, max_length=50)
    extra_data: Optional[dict] = None
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    """Schema de respuesta para Company."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyList(BaseModel):
    """Lista paginada de empresas."""

    items: list[CompanyResponse]
    total: int
    page: int
    per_page: int

    model_config = {"from_attributes": True}
