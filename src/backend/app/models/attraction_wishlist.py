"""AttractionWishlist 景点收藏模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class AttractionWishlist(Base):
    """景点收藏 — 用户和景点之间的收藏关联。"""

    __tablename__ = "attraction_wishlists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    attraction_id = Column(UUID(as_uuid=True), ForeignKey("attractions.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("user_id", "attraction_id", name="uq_user_attraction_wishlist"),)
