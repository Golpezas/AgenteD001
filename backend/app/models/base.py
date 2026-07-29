"""
Base declarativa SQLAlchemy con columnas comunes.

Define el modelo base, el generador de UUID y los mixins
para timestamps y soft delete.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos del proyecto."""

    type_annotation_map = {
        dict: JSON,
    }


def gen_uuid() -> uuid.UUID:
    """Genera un UUID v4 para usar como PK."""
    return uuid.uuid4()


class TimestampMixin:
    """Mixin que agrega created_at y updated_at automáticos."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin que agrega is_active para soft delete."""

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
