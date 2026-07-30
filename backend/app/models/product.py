"""
Modelo Product — Producto/Servicio.

Representa un producto o servicio que puede ser incluido
en listas de precios y propuestas.
"""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, gen_uuid


class Product(Base, TimestampMixin, SoftDeleteMixin):
    """Producto o servicio ofrecido."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Código interno (ej: BAL002, MPE002)",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nombre del producto",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    family: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Familia: Balcony, Zeus, MasPedidos, etc.",
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Categoría: monthly_fee, license, implementation, hours",
    )
    extra_data: Mapped[dict | None] = mapped_column(
        JSON(),
        nullable=True,
        comment="Metadatos flexibles",
    )

    # ── Relaciones ──────────────────────────────────────────────
    company: Mapped["Company | None"] = relationship(back_populates="products")
