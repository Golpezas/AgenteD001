"""add_company_id_to_product: Agregar company_id FK a products

Revision ID: 002
Revises: 001
Create Date: 2026-07-29
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agrega columna company_id a products con FK a companies."""
    op.add_column(
        "products",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_products_company_id",
        "products",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Elimina la FK y la columna company_id de products."""
    op.drop_constraint("fk_products_company_id", "products", type_="foreignkey")
    op.drop_column("products", "company_id")
