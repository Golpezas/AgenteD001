"""
Modelo Notification — Notificación del sistema.

Representa una notificación interna del sistema que puede ser
de tipo system (automática), business (reglas de negocio) o
manual (creada por usuario).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, gen_uuid


class Notification(Base, TimestampMixin, SoftDeleteMixin):
    """Notificación interna del sistema."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="system | business | manual",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Categoría: product, company, policy, price, commercial, etc.",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Título breve de la notificación",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Descripción detallada (opcional)",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        default="info",
        nullable=False,
        comment="info | warning | error | success",
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Tipo del recurso asociado: product, company, etc.",
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="UUID del recurso asociado (string)",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_dismissed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
