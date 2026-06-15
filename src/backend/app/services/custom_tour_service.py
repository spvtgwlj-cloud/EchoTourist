"""自定制旅程业务逻辑服务（支持多段行程）。"""


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.custom_tour import crud_custom_tour_request
from app.models.attraction import AttractionTranslation
from app.models.custom_tour import BaseService, CustomTourRequest
from app.models.destination import DestinationTranslation
from app.models.tour import TourTranslation
from app.models.user import User
from app.schemas.custom_tour import (
    CustomTourCreateRequest,
    CustomTourRequestResponse,
    CustomTourServiceResponse,
    SegmentAttractionResponse,
    SegmentResponse,
    SegmentTourResponse,
)


class CustomTourService:
    """自定制旅程服务。"""

    @staticmethod
    def _calculate_subtotal(
        services_data: list[dict],
        pax_count: int,
        segments: list[dict],  # each has days count
    ) -> tuple[float, dict]:
        """自动计算价格总额。

        价格算法:
        - per_day: unit_price × quantity × sum of segment days
        - per_pax: unit_price × quantity × pax_count
        - per_trip: unit_price × quantity
        """
        total = 0.0
        breakdown = {}
        total_days = sum(seg.get("days", 0) for seg in segments)

        # 基础服务费用计算
        services_total = 0.0
        for svc in services_data:
            unit_price = svc.get("unit_price", 0)
            quantity = svc.get("quantity", 1)
            unit_type = svc.get("unit_type", "per_day")

            if unit_type == "per_day":
                svc_total = unit_price * quantity * total_days
            elif unit_type == "per_pax":
                svc_total = unit_price * quantity * pax_count
            else:  # per_trip
                svc_total = unit_price * quantity

            services_total += svc_total

        total += services_total
        breakdown["services"] = services_total
        breakdown["total_days"] = total_days

        return round(total, 2), breakdown

    async def calculate_quote(
        self,
        db: AsyncSession,
        req: CustomTourCreateRequest,
    ) -> tuple[float, dict]:
        """计算定制旅程报价（基于多段行程）。"""
        segments_data = []
        for seg in req.segments:
            days = max(1, (seg.end_date - seg.start_date).days)
            segments_data.append({"days": days})

        # 构建 services_data（含单价信息）
        services_data = []
        for svc_input in req.services:
            result = await db.execute(
                select(BaseService).where(BaseService.id == svc_input.service_id)
            )
            base_svc = result.scalar_one_or_none()
            if base_svc:
                services_data.append({
                    "unit_price": base_svc.unit_price,
                    "quantity": svc_input.quantity,
                    "unit_type": base_svc.unit_type,
                    "name": base_svc.name,
                })

        subtotal, breakdown = self._calculate_subtotal(
            services_data, req.pax_count, segments_data
        )
        return subtotal, breakdown

    async def submit_request(
        self,
        db: AsyncSession,
        req: CustomTourCreateRequest,
        user: User | None,
    ) -> CustomTourRequest:
        """提交自定制旅程请求（含多段行程）。"""
        # 计算报价
        subtotal, _ = await self.calculate_quote(db, req)

        # 构建 segments_data
        segments_data = []
        for seg in req.segments:
            segments_data.append({
                "destination_id": seg.destination_id,
                "custom_destination": seg.custom_destination,
                "start_date": seg.start_date,
                "end_date": seg.end_date,
                "attraction_ids": seg.attraction_ids,
                "tour_ids": seg.tour_ids,
            })

        # 构建 services_data
        services_data = [
            {"service_id": s.service_id, "quantity": s.quantity}
            for s in req.services
        ]

        request = await crud_custom_tour_request.create_with_relations(
            db,
            request_no=await crud_custom_tour_request.get_request_no(),
            user_id=user.id if user else None,
            pax_count=req.pax_count,
            guide_language=req.guide_language,
            segments_data=segments_data,
            services_data=services_data,
            contact_name=req.contact_name,
            contact_email=req.contact_email,
            contact_phone=req.contact_phone,
            special_requests=req.special_requests,
            subtotal=subtotal,
            currency="USD",
            locale=req.locale,
        )
        return request

    async def build_response(
        self, db: AsyncSession, request: CustomTourRequest
    ) -> CustomTourRequestResponse:
        """构建完整响应（含多段行程名称解析）。"""
        segment_responses = []
        for seg in (request.segments or []):
            # 目的地名称（优先系统目的地，其次自定义）
            dest_name = ""
            if seg.destination_id:
                dest_result = await db.execute(
                    select(DestinationTranslation).where(
                        DestinationTranslation.destination_id == seg.destination_id,
                        DestinationTranslation.locale == request.locale,
                    )
                )
                dest_trans = dest_result.scalar_one_or_none()
                if dest_trans:
                    dest_name = dest_trans.name
                else:
                    # fallback
                    dest_result2 = await db.execute(
                        select(DestinationTranslation).where(
                            DestinationTranslation.destination_id == seg.destination_id,
                        ).limit(1)
                    )
                    dt2 = dest_result2.scalars().first()
                    if dt2:
                        dest_name = dt2.name
            elif seg.custom_destination:
                dest_name = seg.custom_destination

            # 景点名称
            attr_responses = []
            for a in (seg.attractions or []):
                attr_name = ""
                attr_result = await db.execute(
                    select(AttractionTranslation).where(
                        AttractionTranslation.attraction_id == a.attraction_id,
                        AttractionTranslation.locale == request.locale,
                    )
                )
                attr_trans = attr_result.scalar_one_or_none()
                if attr_trans:
                    attr_name = attr_trans.name
                else:
                    attr_result2 = await db.execute(
                        select(AttractionTranslation).where(
                            AttractionTranslation.attraction_id == a.attraction_id,
                        ).limit(1)
                    )
                    at2 = attr_result2.scalars().first()
                    if at2:
                        attr_name = at2.name

                attr_responses.append(SegmentAttractionResponse(
                    id=a.id,
                    attraction_id=a.attraction_id,
                    attraction_name=attr_name,
                    sort_order=a.sort_order or 0,
                ))

            # 已有产品名称
            tour_responses = []
            for t in (seg.selected_tours or []):
                tour_name = ""
                tour_result = await db.execute(
                    select(TourTranslation).where(
                        TourTranslation.tour_id == t.tour_id,
                    ).limit(1)
                )
                tt = tour_result.scalars().first()
                if tt:
                    tour_name = tt.name

                tour_responses.append(SegmentTourResponse(
                    id=t.id,
                    tour_id=t.tour_id,
                    tour_name=tour_name,
                ))

            segment_responses.append(SegmentResponse(
                id=seg.id,
                segment_order=seg.segment_order,
                destination_id=seg.destination_id,
                destination_name=dest_name,
                custom_destination=seg.custom_destination,
                start_date=seg.start_date,
                end_date=seg.end_date,
                attractions=attr_responses,
                selected_tours=tour_responses,
            ))

        # 服务名称
        service_responses = []
        for s in (request.services or []):
            svc_result = await db.execute(
                select(BaseService).where(BaseService.id == s.service_id)
            )
            base_svc = svc_result.scalar_one_or_none()
            svc_name = base_svc.name if base_svc else ""
            unit_type = base_svc.unit_type if base_svc else "per_day"

            service_responses.append(CustomTourServiceResponse(
                id=s.id,
                service_id=s.service_id,
                service_name=svc_name,
                unit_type=unit_type,
                quantity=s.quantity,
                unit_price_snapshot=s.unit_price_snapshot,
                subtotal=s.subtotal,
            ))

        return CustomTourRequestResponse(
            id=request.id,
            request_no=request.request_no,
            user_id=request.user_id,
            pax_count=request.pax_count,
            guide_language=request.guide_language,
            contact_name=request.contact_name,
            contact_email=request.contact_email,
            contact_phone=request.contact_phone,
            special_requests=request.special_requests,
            subtotal=request.subtotal or 0,
            confirmed_price=request.confirmed_price,
            currency=request.currency or "USD",
            status=request.status,
            admin_notes=request.admin_notes,
            locale=request.locale or "en",
            segments=segment_responses,
            services=service_responses,
            created_at=request.created_at.isoformat() if request.created_at else "",
            updated_at=request.updated_at.isoformat() if request.updated_at else "",
        )


custom_tour_service = CustomTourService()
