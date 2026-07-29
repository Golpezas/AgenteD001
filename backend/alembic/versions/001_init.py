"""init: Crear tablas iniciales (companies, products, price_lists, price_list_items, pricing_rules)

Revision ID: 001
Revises:
Create Date: 2026-07-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea las tablas iniciales del sistema."""
    
    # --- Companies ---
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_name", sa.String(255), nullable=False),
        sa.Column("cuit", sa.String(20), nullable=True),
        sa.Column("legal_rep", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("fiscal_address", sa.Text, nullable=True),
        sa.Column("vertical", sa.String(100), nullable=True),
        sa.Column("tech_tier", sa.String(50), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- Products ---
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("family", sa.String(100), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- Price Lists ---
    op.create_table(
        "price_lists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- Price List Items ---
    op.create_table(
        "price_list_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("price_list_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("price_lists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), server_default="ARS", nullable=False),
        sa.Column("effective_from", sa.Date, nullable=False),
        sa.Column("effective_to", sa.Date, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- Pricing Rules ---
    op.create_table(
        "pricing_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("technology_tier", sa.String(50), nullable=True),
        sa.Column("conditions", postgresql.JSONB, nullable=True),
        sa.Column("value", sa.Numeric(10, 4), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- Indexes ---
    op.create_index("ix_companies_business_name", "companies", ["business_name"])
    op.create_index("ix_companies_cuit", "companies", ["cuit"])
    op.create_index("ix_products_code", "products", ["code"])
    op.create_index("ix_products_family", "products", ["family"])
    op.create_index("ix_price_list_items_product", "price_list_items", ["product_id"])
    op.create_index("ix_price_list_items_price_list", "price_list_items", ["price_list_id"])
    op.create_index("ix_pricing_rules_type", "pricing_rules", ["rule_type"])


def downgrade() -> None:
    """Elimina las tablas iniciales."""
    op.drop_table("price_list_items")
    op.drop_table("price_lists")
    op.drop_table("pricing_rules")
    op.drop_table("products")
    op.drop_table("companies")
