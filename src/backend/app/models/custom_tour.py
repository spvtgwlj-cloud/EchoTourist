"""CustomTour 自定制旅程模型。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class BaseService(Base):
    """基础服务 — 最小颗粒度的服务单元，由超管在 Dashboard 录入。
    例如：单程接送机、一天英语导游服务、每人每天车辆服务等。
    """

    __tablename__ = "base_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    name_zh = Column(String(200))
    name_es = Column(String(200))
    name_fr = Column(String(200))
    description = Column(Text)
    description_zh = Column(Text)
    description_es = Column(Text)
    description_fr = Column(Text)
    # unit_type: per_day（按天计费）, per_pax（按人计费）, per_trip（按趟计费）
    unit_type = Column(String(20), nullable=False, default="per_day")
    unit_price = Column(Float, nullable=False, default=0)
    currency = Column(String(3), default="USD")
    category = Column(String(50))  # 分类：guide/transport/hotel/meal/other
    sort_order = Column(SmallInteger, default=0)
    status = Column(String(20), default="active")  # active/inactive
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CustomTourRequest(Base):
    """自定制旅程请求 — 用户提交的定制需求（含多段行程）。"""

    __tablename__ = "custom_tour_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_no = Column(String(30), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # 全局信息
    pax_count = Column(SmallInteger, nullable=False, default=1)
    guide_language = Column(String(100))  # 自由文本 + 前端预设选项
    # 联系信息 — 必填
    contact_name = Column(String(100), nullable=False)
    contact_email = Column(String(200), nullable=False)
    contact_phone = Column(String(30))
    special_requests = Column(Text)
    # 价格
    subtotal = Column(Float, default=0)  # 系统自动计算的价格
    confirmed_price = Column(Float, nullable=True)  # 超管确认价格
    currency = Column(String(3), default="USD")
    # 状态
    status = Column(String(30), nullable=False, default="pending")
    # pending: 待处理, quoted: 已报价, confirmed: 已确认, rejected: 已拒绝, paid: 已支付
    admin_notes = Column(Text)  # 超管备注
    locale = Column(String(10), default="en")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    segments = relationship("CustomTourSegment", back_populates="request",
                            cascade="all, delete-orphan",
                            order_by="CustomTourSegment.segment_order",
                            lazy="selectin")
    services = relationship("CustomTourService", back_populates="request",
                            cascade="all, delete-orphan",
                            lazy="selectin")


class CustomTourSegment(Base):
    """自定制旅程 — 行程段。每段一个目的地 + 时间段 + 选中的已有产品。"""

    __tablename__ = "custom_tour_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(
        UUID(as_uuid=True), ForeignKey("custom_tour_requests.id", ondelete="CASCADE"), nullable=False
    )
    segment_order = Column(SmallInteger, nullable=False, default=1)
    destination_id = Column(
        UUID(as_uuid=True), ForeignKey("destinations.id"), nullable=True
    )
    custom_destination = Column(String(500), nullable=True)  # 客户自行输入的目的地（当 destination_id 为空时使用）
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Relationships
    request = relationship("CustomTourRequest", back_populates="segments")
    destination = relationship("Destination", lazy="selectin")
    selected_tours = relationship("CustomTourSegmentTour", back_populates="segment",
                                  cascade="all, delete-orphan", lazy="selectin")
    attractions = relationship("CustomTourAttraction", back_populates="segment",
                               cascade="all, delete-orphan", lazy="selectin")


class CustomTourSegmentTour(Base):
    """行程段 — 选择的已有产品（多对多，每段可选多个产品）。"""

    __tablename__ = "custom_tour_segment_tours"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(
        UUID(as_uuid=True), ForeignKey("custom_tour_segments.id", ondelete="CASCADE"), nullable=False
    )
    tour_id = Column(
        UUID(as_uuid=True), ForeignKey("tours.id"), nullable=False
    )

    segment = relationship("CustomTourSegment", back_populates="selected_tours")


class CustomTourAttraction(Base):
    """行程段 — 景点关联表。"""

    __tablename__ = "custom_tour_attractions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(
        UUID(as_uuid=True), ForeignKey("custom_tour_segments.id", ondelete="CASCADE"), nullable=False
    )
    attraction_id = Column(
        UUID(as_uuid=True), ForeignKey("attractions.id", ondelete="CASCADE"), nullable=False
    )
    sort_order = Column(SmallInteger, default=0)

    segment = relationship("CustomTourSegment", back_populates="attractions")
    attraction = relationship("Attraction", lazy="selectin")


class CustomTourService(Base):
    """自定制旅程 — 基础服务关联表（带数量和单价快照）。"""

    __tablename__ = "custom_tour_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(
        UUID(as_uuid=True), ForeignKey("custom_tour_requests.id", ondelete="CASCADE"), nullable=False
    )
    service_id = Column(
        UUID(as_uuid=True), ForeignKey("base_services.id"), nullable=False
    )
    quantity = Column(Integer, nullable=False, default=1)  # 数量（份数/天数）
    unit_price_snapshot = Column(Float, nullable=False, default=0)  # 选择时的单价快照
    subtotal = Column(Float, nullable=False, default=0)  # quantity * unit_price_snapshot

    request = relationship("CustomTourRequest", back_populates="services")
    service = relationship("BaseService", lazy="selectin")
