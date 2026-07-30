"""
Modelo BusinessPolicy — Política Comercial.

Define políticas comerciales: descuentos, beneficios, financiamiento y reglas
generales. Cada política se tipifica y puede incluir condiciones en JSONB para
flexibilidad. Aplica a productos y segmentos de clientes con vigencia temporal.
"""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, gen_uuid


class BusinessPolicy(Base, TimestampMixin, SoftDeleteMixin):
    """Política comercial: descuento, beneficio, financiamiento o regla general."""

    __tablename__ = "business_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nombre de la política",
    )
    policy_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Tipo: discount, benefit, financing, policy",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    value: Mapped[float | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="Valor: porcentaje descuento, monto fijo, etc.",
    )
    value_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Tipo de valor: percentage, fixed_amount",
    )
    conditions: Mapped[dict | None] = mapped_column(
        JSON(),
        nullable=True,
        comment="Condiciones de aplicación (JSONB)",
    )
    extra_data: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON(),
        nullable=True,
        comment="Metadatos flexibles",
    )
    client_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Tipo de cliente al que aplica",
    )
    effective_from: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Inicio de vigencia",
    )
    effective_to: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="Fin de vigencia",
    )
