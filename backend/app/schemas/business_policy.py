"""
Schemas para BusinessPolicy — creación, respuesta y listado paginado.

Valida policy_type y value_type mediante Literal para evitar valores inválidos.
"""

from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BusinessPolicyCreate(BaseModel):
    """Schema para crear una política comercial."""

    name: str = Field(..., min_length=1, max_length=255)
    policy_type: Literal["discount", "benefit", "financing", "policy"]
    description: Optional[str] = None
    value: Optional[float] = Field(None, ge=-99999.9999, le=99999.9999)
    value_type: Optional[Literal["percentage", "fixed_amount"]] = None
    conditions: Optional[dict] = None
    client_type: Optional[str] = Field(None, max_length=50)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None


class BusinessPolicyUpdate(BaseModel):
    """Schema para actualizar una política comercial."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    policy_type: Optional[Literal["discount", "benefit", "financing", "policy"]] = None
    description: Optional[str] = None
    value: Optional[float] = Field(None, ge=-99999.9999, le=99999.9999)
    value_type: Optional[Literal["percentage", "fixed_amount"]] = None
    conditions: Optional[dict] = None
    client_type: Optional[str] = Field(None, max_length=50)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None


class BusinessPolicyResponse(BaseModel):
    """Schema de respuesta para BusinessPolicy."""

    id: UUID
    name: str
    policy_type: str
    description: Optional[str] = None
    value: Optional[float] = None
    value_type: Optional[str] = None
    conditions: Optional[dict] = None
    client_type: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BusinessPolicyList(BaseModel):
    """Lista paginada de políticas comerciales."""

    items: list[BusinessPolicyResponse]
    total: int
    page: int
    per_page: int

    model_config = {"from_attributes": True}
