"""add theme column to tours

Revision ID: a1b2c3d4e5f6
Revises: 31459b62fab7
Create Date: 2026-06-06 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '31459b62fab7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tours', sa.Column('theme', sa.String(30), nullable=True))
    # 为现有数据设置默认主题
    op.execute("UPDATE tours SET theme = 'culture_history' WHERE theme IS NULL")
    # 添加 NOT NULL 约束
    op.alter_column('tours', 'theme', nullable=False, server_default='citywalk')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tours', 'theme')
