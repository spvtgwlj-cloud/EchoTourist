"""Enquiry 咨询表单模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Enquiry(Base):
    """咨询/询价表单记录"""
    __tablename__ = "enquiries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    destination = Column(String(200))          # 感兴趣的目的地
    pax_count = Column(Integer)                # 出行人数
    message = Column(Text, nullable=False)      # 需求描述
    status = Column(String(20), nullable=False, default="new")  # new | read | contacted | closed
    admin_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
