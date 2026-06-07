"""add_tour_sort_order

Revision ID: 13ba84d9cf34
Revises: 04e188fec6fc
Create Date: 2026-06-05 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13ba84d9cf34'
down_revision: Union[str, None] = '04e188fec6fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tours", sa.Column("sort_order", sa.SmallInteger(), server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("tours", "sort_order")
