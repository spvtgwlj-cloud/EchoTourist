"""Destination 目的地模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Destination(Base):
    __tablename__ = "destinations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    area_code = Column(String(10))  # 城市电话区号，如 010/025/029
    image_url = Column(String(500))
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    translations = relationship("DestinationTranslation", backref="destination", lazy="selectin")


class DestinationTranslation(Base):
    __tablename__ = "destination_translations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination_id = Column(
        UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="CASCADE"), nullable=False
    )
    locale = Column(String(10), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    meta_title = Column(String(200))
    meta_description = Column(String(300))
