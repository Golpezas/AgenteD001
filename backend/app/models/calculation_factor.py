"""
Modelo CalculationFactor — Factor de Licenciamiento.

Define factores multiplicadores de precio por concepto y technology tier
(Express, Advanced, Premium). Cada factor es un valor numérico (x5, x2, x1, x6, x3)
que se aplica al precio base de productos según el concepto de licenciamiento.
"""

import uuid

from sqlalchemy import Boolean, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, gen_uuid


class CalculationFactor(Base, TimestampMixin, SoftDeleteMixin):
    """Factor multiplicador de precio por concepto y technology tier."""

    __tablename__ = "calculation_factors"
    __table_args__ = (
        UniqueConstraint(
            "concept_key",
            "technology_tier",
            name="uq_calc_factor_concept_tier",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    concept_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Clave del concepto (ej: accesos_simultaneos)",
    )
    concept_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Nombre legible del concepto",
    )
    technology_tier: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Tier: Express, Advanced, Premium",
    )
    factor: Mapped[float | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="Factor multiplicador. NULL = requires_quote",
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    extra_data: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON(),
        nullable=True,
        comment="Metadatos flexibles (ej: requires_quote, notas internas)",
    )
