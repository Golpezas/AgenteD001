"""
Modelo Company — Empresa/Cliente.

Representa una empresa o cliente del sistema con datos
genéricos y un campo JSONB para metadatos flexibles.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, gen_uuid


class Company(Base, TimestampMixin, SoftDeleteMixin):
    """Empresa o cliente del sistema."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    business_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Razón social",
    )
    cuit: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="CUIT",
    )
    legal_rep: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Representante legal",
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    fiscal_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Domicilio fiscal",
    )
    vertical: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Vertical de negocio (Ej: Pinturería)",
    )
    tech_tier: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Tier tecnológico: Express / Advanced / Premium",
    )
    extra_data: Mapped[dict | None] = mapped_column(
        JSON(),
        nullable=True,
        comment="Metadatos flexibles (campos específicos del negocio)",
    )
