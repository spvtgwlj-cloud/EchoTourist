"""Review 评价模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id = Column(UUID(as_uuid=True), ForeignKey("tours.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rating = Column(SmallInteger, nullable=False)  # 1-5
    title = Column(String(200))
    comment = Column(Text)
    locale = Column(String(10), default="en")
    status = Column(String(20), default="pending")  # pending | approved | rejected
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    tour = relationship("Tour", backref="reviews_list")
    user = relationship("User", backref="reviews")
