"""
Schemas para PricingRule — creación y respuesta.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PricingRuleCreate(BaseModel):
    """Schema para crear una regla de precio."""

    name: str = Field(..., min_length=1, max_length=255)
    rule_type: str = Field(..., max_length=50)
    technology_tier: Optional[str] = Field(None, max_length=50)
    conditions: Optional[dict] = None
    value: float = Field(..., ge=0)
    description: Optional[str] = None


class PricingRuleUpdate(BaseModel):
    """Schema para actualizar una regla de precio."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    rule_type: Optional[str] = Field(None, max_length=50)
    technology_tier: Optional[str] = Field(None, max_length=50)
    conditions: Optional[dict] = None
    value: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PricingRuleResponse(BaseModel):
    """Schema de respuesta para PricingRule."""

    id: UUID
    name: str
    rule_type: str
    technology_tier: Optional[str]
    conditions: Optional[dict]
    value: float
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
