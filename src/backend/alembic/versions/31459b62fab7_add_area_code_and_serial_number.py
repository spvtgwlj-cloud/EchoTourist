"""add area_code to destinations and serial_number to tours

Revision ID: 31459b62fab7
Revises: d1e956a7b8c9
Create Date: 2026-06-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31459b62fab7'
down_revision: Union[str, None] = 'd1e956a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = '13ba84d9cf34'


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('destinations', sa.Column('area_code', sa.String(10), nullable=True))
    op.add_column('tours', sa.Column('serial_number', sa.String(10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tours', 'serial_number')
    op.drop_column('destinations', 'area_code')
