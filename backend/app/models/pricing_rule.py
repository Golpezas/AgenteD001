"""
Modelo PricingRule — Reglas de Precio.

Define reglas de descuento, factores de licenciamiento y políticas
comerciales que se aplican durante el cálculo de precios.
"""

import uuid
from datetime import datetime

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, gen_uuid


class PricingRule(Base, TimestampMixin, SoftDeleteMixin):
    """Regla de precio: descuento, factor, política o beneficio."""

    __tablename__ = "pricing_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nombre de la regla (ej: Descuento Canal Digital)",
    )
    rule_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Tipo: discount / factor / policy / benefit",
    )
    technology_tier: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Tier al que aplica: Express / Advanced / Premium / all",
    )
    conditions: Mapped[dict | None] = mapped_column(
        JSON(),
        nullable=True,
        comment="Condiciones de aplicación (JSONB)",
    )
    value: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        comment="Valor: porcentaje de descuento, factor multiplicador, etc.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
