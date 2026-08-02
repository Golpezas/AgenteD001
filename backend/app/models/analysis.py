"""
Modelos de Análisis de Imágenes y URLs.

Define los modelos SQLAlchemy para el pipeline de análisis:
AnalysisJob (trabajo de análisis), AnalysisResult (resultado/propuesta)
y ScrapedSource (fuente URL para monitoreo periódico).
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, gen_uuid


class AnalysisStatus(str, Enum):
    """Estados del ciclo de vida de un AnalysisJob."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisJob(Base, TimestampMixin, SoftDeleteMixin):
    """Trabajo de análisis de imagen o URL."""

    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    job_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="image | url",
    )
    input_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Datos de entrada: URL o referencia de imagen",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="pending | processing | completed | failed",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Inicio de procesamiento del job",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Fin de procesamiento del job (éxito o error)",
    )
    result_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        comment="FK al resultado del análisis",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class AnalysisResult(Base, TimestampMixin, SoftDeleteMixin):
    """Resultado de un análisis — propuesta de upsert revisable."""

    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="proposal",
        nullable=False,
        comment="proposal | accepted | rejected",
    )
    product_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    extracted_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    currency: Mapped[str | None] = mapped_column(
        String(3),
        nullable=True,
        comment="Código de moneda ISO 4217",
    )
    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    raw_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Respuesta cruda de Gemini Vision",
    )
    proposal_data: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Propuesta estructurada para revisión",
    )

    # ── Relaciones ──────────────────────────────────────
    job: Mapped["AnalysisJob"] = relationship(
        foreign_keys=[job_id],
    )


class ScrapedSource(Base, TimestampMixin, SoftDeleteMixin):
    """Fuente URL para monitoreo periódico de análisis."""

    __tablename__ = "scraped_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=gen_uuid,
    )
    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        unique=True,
    )
    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    schedule_interval_minutes: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Intervalo de monitoreo en minutos",
    )
    last_analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<ScrapedSource(url={self.url!r}, is_active={self.is_active})>"
