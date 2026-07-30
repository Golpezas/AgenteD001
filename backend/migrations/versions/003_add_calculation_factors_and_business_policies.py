"""add_calculation_factors_and_business_policies: Crear tablas de factores y políticas

Revision ID: 003
Revises: 002
Create Date: 2026-07-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea las tablas calculation_factors y business_policies."""

    # --- Calculation Factors ---
    op.create_table(
        "calculation_factors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("concept_key", sa.String(100), nullable=False),
        sa.Column("concept_name", sa.String(255), nullable=False),
        sa.Column("technology_tier", sa.String(50), nullable=False),
        sa.Column("factor", sa.Numeric(10, 4), nullable=True),
        sa.Column("is_available", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint(
        "uq_calc_factor_concept_tier",
        "calculation_factors",
        ["concept_key", "technology_tier"],
    )
    op.create_index(
        "ix_calculation_factors_concept_key",
        "calculation_factors",
        ["concept_key"],
    )
    op.create_index(
        "ix_calculation_factors_technology_tier",
        "calculation_factors",
        ["technology_tier"],
    )

    # --- Business Policies ---
    op.create_table(
        "business_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("policy_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("value", sa.Numeric(10, 4), nullable=True),
        sa.Column("value_type", sa.String(50), nullable=True),
        sa.Column("conditions", postgresql.JSONB, nullable=True),
        sa.Column("client_type", sa.String(50), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("effective_from", sa.Date, nullable=True),
        sa.Column("effective_to", sa.Date, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_business_policies_policy_type",
        "business_policies",
        ["policy_type"],
    )
    op.create_index(
        "ix_business_policies_client_type",
        "business_policies",
        ["client_type"],
    )


def downgrade() -> None:
    """Elimina las tablas calculation_factors y business_policies."""
    op.drop_table("business_policies")
    op.drop_table("calculation_factors")
