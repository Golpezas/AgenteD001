"""
Modelos PriceList y PriceListItem — Listas de Precios.

Representa una lista de precios y sus ítems asociados a productos.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, gen_uuid


class PriceList(Base, TimestampMixin, SoftDeleteMixin):
    """Lista de precios (ej: Lista Standard, Lista VIP, Lista Partners)."""

    __tablename__ = "price_lists"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nombre de la lista de precios",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Relaciones
    items: Mapped[list["PriceListItem"]] = relationship(
        back_populates="price_list",
        cascade="all, delete-orphan",
    )


class PriceListItem(Base, TimestampMixin, SoftDeleteMixin):
    """Ítem dentro de una lista de precios."""

    __tablename__ = "price_list_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    price_list_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("price_lists.id", ondelete="CASCADE"),
        nullable=False,
    )
    price: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Precio del producto en esta lista",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="ARS",
        nullable=False,
        comment="Moneda: ARS / EUR / USD",
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Fecha desde la que aplica este precio",
    )
    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Fecha hasta la que aplica (null = vigencia indefinida)",
    )
    extra_data: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON(),
        nullable=True,
    )

    # Relaciones
    product: Mapped["Product"] = relationship(
        backref="price_list_items",
    )
    price_list: Mapped["PriceList"] = relationship(
        back_populates="items",
    )
