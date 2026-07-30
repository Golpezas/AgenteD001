"""
Schemas para Notification — creación, actualización y respuesta.
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    """Campos base compartidos para notificaciones."""

    type: Literal["system", "business", "manual"] = Field(...)
    category: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    severity: Literal["info", "warning", "error", "success"] = Field(default="info")
    resource_type: Optional[str] = Field(None, max_length=50)
    resource_id: Optional[str] = Field(None, max_length=36)


class NotificationCreate(NotificationBase):
    """Schema para crear una notificación."""

    pass


class NotificationUpdate(BaseModel):
    """Schema para actualizar una notificación (marcar leída/descartada)."""

    is_read: Optional[bool] = None
    is_dismissed: Optional[bool] = None


class NotificationResponse(NotificationBase):
    """Schema de respuesta para Notification."""

    id: UUID
    is_read: bool
    is_dismissed: bool
    read_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationList(BaseModel):
    """Lista paginada de notificaciones."""

    items: list[NotificationResponse]
    total: int
    page: int
    per_page: int

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    """Respuesta con conteo de no leídas."""

    count: int
