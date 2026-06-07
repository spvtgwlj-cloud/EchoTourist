"""add_custom_tour_models (自定制旅程 — 支持多段行程)

Revision ID: d1e956a7b8c9
Revises: 04e188fec6fc
Create Date: 2026-06-06 04:34:54.750937
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e956a7b8c9'
down_revision: Union[str, None] = '04e188fec6fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### 基础服务表 ###
    op.create_table('base_services',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('name_zh', sa.String(length=200), nullable=True),
        sa.Column('name_es', sa.String(length=200), nullable=True),
        sa.Column('name_fr', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('description_zh', sa.Text(), nullable=True),
        sa.Column('description_es', sa.Text(), nullable=True),
        sa.Column('description_fr', sa.Text(), nullable=True),
        sa.Column('unit_type', sa.String(length=20), nullable=False, server_default='per_day'),
        sa.Column('unit_price', sa.Float(), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=3), nullable=True, server_default='USD'),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('sort_order', sa.SmallInteger(), nullable=True, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=True, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_base_services_status'), 'base_services', ['status'], unique=False)
    op.create_index(op.f('ix_base_services_category'), 'base_services', ['category'], unique=False)

    # ### 自定制旅程请求表（全局信息） ###
    op.create_table('custom_tour_requests',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('request_no', sa.String(length=30), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('pax_count', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('guide_language', sa.String(length=100), nullable=True),
        sa.Column('contact_name', sa.String(length=100), nullable=False),
        sa.Column('contact_email', sa.String(length=200), nullable=False),
        sa.Column('contact_phone', sa.String(length=30), nullable=True),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('subtotal', sa.Float(), nullable=True, server_default='0'),
        sa.Column('confirmed_price', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True, server_default='USD'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('locale', sa.String(length=10), nullable=True, server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_custom_tour_requests_request_no'), 'custom_tour_requests', ['request_no'], unique=True)
    op.create_index(op.f('ix_custom_tour_requests_status'), 'custom_tour_requests', ['status'], unique=False)
    op.create_index(op.f('ix_custom_tour_requests_user_id'), 'custom_tour_requests', ['user_id'], unique=False)

    # ### 行程段表 ###
    op.create_table('custom_tour_segments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('request_id', sa.UUID(), nullable=False),
        sa.Column('segment_order', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('destination_id', sa.UUID(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['request_id'], ['custom_tour_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['destination_id'], ['destinations.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_custom_tour_segments_request_id'), 'custom_tour_segments', ['request_id'], unique=False)

    # ### 行程段 — 已有产品关联表 ###
    op.create_table('custom_tour_segment_tours',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('segment_id', sa.UUID(), nullable=False),
        sa.Column('tour_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['segment_id'], ['custom_tour_segments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tour_id'], ['tours.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_custom_tour_segment_tours_segment_id'), 'custom_tour_segment_tours', ['segment_id'], unique=False)

    # ### 行程段 — 景点关联表 ###
    op.create_table('custom_tour_attractions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('segment_id', sa.UUID(), nullable=False),
        sa.Column('attraction_id', sa.UUID(), nullable=False),
        sa.Column('sort_order', sa.SmallInteger(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['attraction_id'], ['attractions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['segment_id'], ['custom_tour_segments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_custom_tour_attractions_segment_id'), 'custom_tour_attractions', ['segment_id'], unique=False)

    # ### 定制旅程 — 基础服务关联表 ###
    op.create_table('custom_tour_services',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('request_id', sa.UUID(), nullable=False),
        sa.Column('service_id', sa.UUID(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_price_snapshot', sa.Float(), nullable=False, server_default='0'),
        sa.Column('subtotal', sa.Float(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['request_id'], ['custom_tour_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_id'], ['base_services.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_custom_tour_services_request_id'), 'custom_tour_services', ['request_id'], unique=False)


def downgrade() -> None:
    op.drop_table('custom_tour_services')
    op.drop_table('custom_tour_attractions')
    op.drop_table('custom_tour_segment_tours')
    op.drop_table('custom_tour_segments')
    op.drop_table('custom_tour_requests')
    op.drop_table('base_services')
