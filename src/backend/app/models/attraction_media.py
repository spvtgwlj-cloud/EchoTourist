"""AttractionMedia 景点多媒体资源（照片/短视频）模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class AttractionMedia(Base):
    """景点多媒体资源 — 每个景点最多关联 8 张照片或短视频。"""

    __tablename__ = "attraction_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attraction_id = Column(
        UUID(as_uuid=True), ForeignKey("attractions.id", ondelete="CASCADE"), nullable=False
    )
    url = Column(String(500), nullable=False)
    media_type = Column(String(10), nullable=False, default="image")  # "image" | "video"
    alt_text = Column(String(300))
    sort_order = Column(SmallInteger, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    attraction = relationship("Attraction", back_populates="media")
