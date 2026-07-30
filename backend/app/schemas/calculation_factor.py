"""
Schemas para CalculationFactor — creación, respuesta y listado paginado.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CalculationFactorCreate(BaseModel):
    """Schema para crear un factor de licenciamiento."""

    concept_key: str = Field(..., min_length=1, max_length=100)
    concept_name: str = Field(..., min_length=1, max_length=255)
    technology_tier: str = Field(..., max_length=50)
    factor: Optional[float] = Field(None, ge=-99999.9999, le=99999.9999)
    is_available: Optional[bool] = None
    extra_data: Optional[dict] = None


class CalculationFactorUpdate(BaseModel):
    """Schema para actualizar un factor de licenciamiento."""

    concept_key: Optional[str] = Field(None, min_length=1, max_length=100)
    concept_name: Optional[str] = Field(None, min_length=1, max_length=255)
    technology_tier: Optional[str] = Field(None, max_length=50)
    factor: Optional[float] = Field(None, ge=-99999.9999, le=99999.9999)
    is_available: Optional[bool] = None
    extra_data: Optional[dict] = None


class CalculationFactorResponse(BaseModel):
    """Schema de respuesta para CalculationFactor."""

    id: UUID
    concept_key: str
    concept_name: str
    technology_tier: str
    factor: Optional[float] = None
    is_available: bool
    extra_data: Optional[dict] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CalculationFactorList(BaseModel):
    """Lista paginada de factores de licenciamiento."""

    items: list[CalculationFactorResponse]
    total: int
    page: int
    per_page: int

    model_config = {"from_attributes": True}
