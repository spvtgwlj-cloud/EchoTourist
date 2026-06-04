"""initial schema - capture all model tables

Revision ID: 5bf1e9edbde4
Revises: af36124973cc
Create Date: 2026-06-04 05:29:25.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "5bf1e9edbde4"
down_revision: Union[str, None] = "af36124973cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255)),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("google_id", sa.String(255), unique=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_admin", sa.Boolean(), default=False),
        sa.Column("locale", sa.String(10), default="en"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    # --- destinations ---
    op.create_table(
        "destinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("image_url", sa.String(500)),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- destination_translations ---
    op.create_table(
        "destination_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("meta_title", sa.String(200)),
        sa.Column("meta_description", sa.String(300)),
    )

    # --- tours ---
    op.create_table(
        "tours",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(200), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, default="draft"),
        sa.Column("type", sa.String(30), nullable=False, default="group_tour"),
        sa.Column("duration_days", sa.SmallInteger(), nullable=False),
        sa.Column("duration_nights", sa.SmallInteger(), nullable=False, default=0),
        sa.Column("max_pax", sa.SmallInteger()),
        sa.Column("min_pax", sa.SmallInteger(), default=1),
        sa.Column("start_price", sa.Float(), default=0),
        sa.Column("currency", sa.String(3), default="USD"),
        sa.Column("difficulty", sa.String(20), default="easy"),
        sa.Column("highlights", postgresql.ARRAY(sa.Text()), default=list),
        sa.Column("includes", postgresql.ARRAY(sa.Text()), default=list),
        sa.Column("excludes", postgresql.ARRAY(sa.Text()), default=list),
        sa.Column("destination_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list),
        sa.Column("avg_rating", sa.Float(), default=0),
        sa.Column("review_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )

    # --- tour_translations ---
    op.create_table(
        "tour_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tour_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tours.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("subtitle", sa.String(500)),
        sa.Column("description", sa.Text()),
        sa.Column("itinerary", postgresql.JSON()),
        sa.Column("meta_title", sa.String(200)),
        sa.Column("meta_description", sa.String(300)),
    )

    # --- tour_dates ---
    op.create_table(
        "tour_dates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tour_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tours.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("price_per_pax", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), default="USD"),
        sa.Column("availability", sa.SmallInteger(), nullable=False, default=0),
        sa.Column("status", sa.String(20), default="available"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- tour_images ---
    op.create_table(
        "tour_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tour_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tours.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("alt_text", sa.String(300)),
        sa.Column("sort_order", sa.SmallInteger(), default=0),
    )

    # --- orders ---
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_no", sa.String(30), unique=True, nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id")),
        sa.Column("tour_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tours.id"), nullable=False),
        sa.Column("tour_date_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tour_dates.id")),
        sa.Column("status", sa.String(30), nullable=False, default="pending"),
        sa.Column("pax_count", sa.SmallInteger(), nullable=False),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.Column("discount", sa.Float(), default=0),
        sa.Column("tax", sa.Float(), default=0),
        sa.Column("total", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), default="USD"),
        sa.Column("contact_name", sa.String(100)),
        sa.Column("contact_email", sa.String(200)),
        sa.Column("contact_phone", sa.String(30)),
        sa.Column("special_requests", sa.Text()),
        sa.Column("source", sa.String(30), default="web"),
        sa.Column("locale", sa.String(10), default="en"),
        sa.Column("stripe_session_id", sa.String(255)),
        sa.Column("payment_status", sa.String(30), default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- order_passengers ---
    op.create_table(
        "order_passengers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("passport_number", sa.String(50)),
        sa.Column("special_requirements", sa.Text()),
    )

    # --- reviews ---
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tour_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tours.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.String(200)),
        sa.Column("comment", sa.Text()),
        sa.Column("locale", sa.String(10), default="en"),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- wishlists ---
    op.create_table(
        "wishlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tour_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tours.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "tour_id", name="uq_user_tour_wishlist"),
    )

    # --- attractions ---
    op.create_table(
        "attractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("destination_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("image_url", sa.String(500)),
        sa.Column("sort_order", sa.SmallInteger(), default=0),
        sa.Column("rating", sa.SmallInteger(), default=0),
        sa.Column("status", sa.String(20), default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- attraction_translations ---
    op.create_table(
        "attraction_translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("attraction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("attractions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("ticket_info", sa.String(300)),
        sa.Column("opening_hours", sa.String(200)),
        sa.Column("meta_title", sa.String(200)),
        sa.Column("meta_description", sa.String(300)),
    )


def downgrade() -> None:
    op.drop_table("attraction_translations")
    op.drop_table("attractions")
    op.drop_table("wishlists")
    op.drop_table("reviews")
    op.drop_table("order_passengers")
    op.drop_table("orders")
    op.drop_table("tour_images")
    op.drop_table("tour_dates")
    op.drop_table("tour_translations")
    op.drop_table("tours")
    op.drop_table("destination_translations")
    op.drop_table("destinations")
    op.drop_table("users")
