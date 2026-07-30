"""add notifications table

Revision ID: 004
Revises: 003
Create Date: 2026-07-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea la tabla notifications."""
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(20), nullable=False, comment="system | business | manual"),
        sa.Column("category", sa.String(50), nullable=False, comment="Categoría: product, company, policy, price, commercial"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("severity", sa.String(20), server_default="info", nullable=False, comment="info | warning | error | success"),
        sa.Column("resource_type", sa.String(50), nullable=True, comment="Tipo del recurso asociado"),
        sa.Column("resource_id", sa.String(36), nullable=True, comment="UUID del recurso asociado"),
        sa.Column("is_read", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("is_dismissed", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Índices para consultas frecuentes
    op.create_index("ix_notifications_type", "notifications", ["type"])
    op.create_index("ix_notifications_category", "notifications", ["category"])
    op.create_index("ix_notifications_is_read_created", "notifications", ["is_read", "created_at"])
    op.create_index("ix_notifications_resource", "notifications", ["resource_type", "resource_id"])


def downgrade() -> None:
    """Elimina la tabla notifications."""
    op.drop_index("ix_notifications_resource")
    op.drop_index("ix_notifications_is_read_created")
    op.drop_index("ix_notifications_category")
    op.drop_index("ix_notifications_type")
    op.drop_table("notifications")
