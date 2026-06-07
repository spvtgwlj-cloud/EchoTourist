"""自定制旅程 CRUD 操作（支持多段行程）。"""

from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.custom_tour import (
    BaseService,
    CustomTourRequest,
    CustomTourSegment,
    CustomTourSegmentTour,
    CustomTourAttraction,
    CustomTourService,
)


crud_base_service = CRUDBase(BaseService)
crud_custom_tour = CRUDBase(CustomTourRequest)


class CRUDCustomTourRequest(CRUDBase[CustomTourRequest]):
    """自定制旅程请求 CRUD（含多段行程关联操作）。"""

    async def create_with_relations(
        self,
        db: AsyncSession,
        *,
        request_no: str,
        user_id: UUID | None,
        pax_count: int,
        guide_language: str | None,
        segments_data: list[dict],  # each with destination_id, start_date, end_date, attraction_ids, tour_ids
        services_data: list[dict],  # each with service_id, quantity
        contact_name: str,
        contact_email: str,
        contact_phone: str | None,
        special_requests: str | None,
        subtotal: float,
        currency: str,
        locale: str,
    ) -> CustomTourRequest:
        """创建自定制旅程请求（含多段行程、景点、产品、服务关联）。"""
        request = CustomTourRequest(
            request_no=request_no,
            user_id=user_id,
            pax_count=pax_count,
            guide_language=guide_language,
            contact_name=contact_name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            special_requests=special_requests,
            subtotal=subtotal,
            currency=currency,
            status="pending",
            locale=locale,
        )
        db.add(request)
        await db.flush()

        # 创建多段行程
        for idx, seg in enumerate(segments_data):
            segment = CustomTourSegment(
                request_id=request.id,
                segment_order=idx + 1,
                destination_id=seg.get("destination_id"),
                custom_destination=seg.get("custom_destination"),
                start_date=seg["start_date"],
                end_date=seg["end_date"],
            )
            db.add(segment)
            await db.flush()

            # 添加景点关联
            for attr_idx, attr_id in enumerate(seg.get("attraction_ids", [])):
                db.add(CustomTourAttraction(
                    segment_id=segment.id,
                    attraction_id=attr_id,
                    sort_order=attr_idx,
                ))

            # 添加已有产品关联（多选）
            for tour_id in seg.get("tour_ids", []):
                db.add(CustomTourSegmentTour(
                    segment_id=segment.id,
                    tour_id=tour_id,
                ))

        # 添加基础服务关联
        for svc in services_data:
            service_id = svc["service_id"]
            quantity = svc.get("quantity", 1)
            svc_result = await db.execute(
                select(BaseService).where(BaseService.id == service_id)
            )
            base_svc = svc_result.scalar_one_or_none()
            unit_price = base_svc.unit_price if base_svc else 0

            db.add(CustomTourService(
                request_id=request.id,
                service_id=service_id,
                quantity=quantity,
                unit_price_snapshot=unit_price,
                subtotal=unit_price * quantity,
            ))

        await db.flush()
        return request

    async def get_with_relations(
        self, db: AsyncSession, request_id: UUID
    ) -> CustomTourRequest | None:
        """获取定制请求完整信息（含多段行程、景点、产品、服务）。"""
        result = await db.execute(
            select(CustomTourRequest).where(CustomTourRequest.id == request_id)
        )
        request = result.scalar_one_or_none()
        if not request:
            return None

        # 加载多段行程
        seg_result = await db.execute(
            select(CustomTourSegment)
            .where(CustomTourSegment.request_id == request_id)
            .order_by(CustomTourSegment.segment_order)
        )
        segments = list(seg_result.scalars().all())
        request.segments = segments

        # 加载每段的景点和产品
        for seg in segments:
            # 景点
            attr_result = await db.execute(
                select(CustomTourAttraction)
                .where(CustomTourAttraction.segment_id == seg.id)
                .order_by(CustomTourAttraction.sort_order)
            )
            seg.attractions = list(attr_result.scalars().all())

            # 已有产品
            tour_result = await db.execute(
                select(CustomTourSegmentTour)
                .where(CustomTourSegmentTour.segment_id == seg.id)
            )
            seg.selected_tours = list(tour_result.scalars().all())

        # 加载服务
        svc_result = await db.execute(
            select(CustomTourService)
            .where(CustomTourService.request_id == request_id)
        )
        request.services = list(svc_result.scalars().all())

        return request

    async def list_by_user(
        self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> list[CustomTourRequest]:
        result = await db.execute(
            select(CustomTourRequest)
            .where(CustomTourRequest.user_id == user_id)
            .order_by(CustomTourRequest.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_request_no(self) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        from uuid import uuid4
        suffix = str(uuid4())[:8].upper()
        return f"CT-{ts}-{suffix}"


crud_custom_tour_request = CRUDCustomTourRequest(CustomTourRequest)
