"""merge tour_sort_order and enquiries_table branches

Revision ID: c2bd43b70559
Revises: 13ba84d9cf34, f7e8d9c0b1a2
Create Date: 2026-06-15 09:35:39.668874
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2bd43b70559'
down_revision: Union[str, None] = ('13ba84d9cf34', 'f7e8d9c0b1a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
