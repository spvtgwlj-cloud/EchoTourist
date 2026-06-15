"""add attraction_media table

Revision ID: 87d127812610
Revises: c2bd43b70559
Create Date: 2026-06-15 09:38:38.967605
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87d127812610'
down_revision: Union[str, None] = 'c2bd43b70559'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('attraction_media',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('attraction_id', sa.UUID(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('media_type', sa.String(length=10), nullable=False),
        sa.Column('alt_text', sa.String(length=300), nullable=True),
        sa.Column('sort_order', sa.SmallInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['attraction_id'], ['attractions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('attraction_media')
