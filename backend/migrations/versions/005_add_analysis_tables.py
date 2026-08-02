"""add analysis tables

Revision ID: 005
Revises: 004
Create Date: 2026-07-31
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea las tablas del pipeline de análisis (jobs, results, sources)."""
    op.create_table(
        "analysis_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_type", sa.String(20), nullable=False, comment="image | url"),
        sa.Column("input_data", sa.JSON, nullable=False, comment="Datos de entrada: URL o referencia de imagen"),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False, comment="pending | processing | completed | failed"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True, comment="Inicio de procesamiento del job"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True, comment="Fin de procesamiento del job (éxito o error)"),
        sa.Column("result_id", postgresql.UUID(as_uuid=True), nullable=True, comment="FK al resultado del análisis"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "analysis_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), server_default="proposal", nullable=False, comment="proposal | accepted | rejected"),
        sa.Column("product_name", sa.String(255), nullable=True),
        sa.Column("extracted_price", sa.Float, nullable=True),
        sa.Column("currency", sa.String(3), nullable=True, comment="Código de moneda ISO 4217"),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("raw_data", sa.JSON, nullable=True, comment="Respuesta cruda de Gemini Vision"),
        sa.Column("proposal_data", sa.JSON, nullable=True, comment="Propuesta estructurada para revisión"),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "scraped_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.String(2048), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("schedule_interval_minutes", sa.Integer, nullable=True, comment="Intervalo de monitoreo en minutos"),
        sa.Column("last_analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Índices por patrón de consulta real (no declarados en el modelo)
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status"])
    op.create_index("ix_analysis_results_status", "analysis_results", ["status"])
    op.create_index("ix_analysis_results_job_id", "analysis_results", ["job_id"])
    op.create_index("ix_scraped_sources_is_active", "scraped_sources", ["is_active"])


def downgrade() -> None:
    """Elimina las tablas del pipeline de análisis."""
    op.drop_index("ix_scraped_sources_is_active")
    op.drop_index("ix_analysis_results_job_id")
    op.drop_index("ix_analysis_results_status")
    op.drop_index("ix_analysis_jobs_status")
    op.drop_table("scraped_sources")
    op.drop_table("analysis_results")
    op.drop_table("analysis_jobs")
