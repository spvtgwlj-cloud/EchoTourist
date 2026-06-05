"""add highlights/includes/excludes to tour_translations

Revision ID: 394f8a2b1c6d
Revises: 5bf1e9edbde4
Create Date: 2026-06-05 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "394f8a2b1c6d"
down_revision: Union[str, None] = "5bf1e9edbde4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add highlights, includes, excludes JSON columns to tour_translations."""
    op.add_column(
        "tour_translations",
        sa.Column("highlights", postgresql.JSON, nullable=True),
    )
    op.add_column(
        "tour_translations",
        sa.Column("includes", postgresql.JSON, nullable=True),
    )
    op.add_column(
        "tour_translations",
        sa.Column("excludes", postgresql.JSON, nullable=True),
    )


def downgrade() -> None:
    """Remove highlights, includes, excludes columns from tour_translations."""
    op.drop_column("tour_translations", "excludes")
    op.drop_column("tour_translations", "includes")
    op.drop_column("tour_translations", "highlights")
