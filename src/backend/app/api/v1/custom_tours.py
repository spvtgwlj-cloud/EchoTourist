"""自定制旅程 API（用户端，支持多段行程）。"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.database import get_db
from app.api.dependencies import get_current_user_optional
from app.models.user import User
from app.crud.custom_tour import crud_base_service, crud_custom_tour_request
from app.schemas.custom_tour import (
    BaseServiceResponse,
    BaseServiceListResponse,
    CustomTourCreateRequest,
    CustomTourRequestResponse,
    CustomTourRequestListResponse,
    CustomTourQuoteResponse,
)
from app.services.custom_tour_service import custom_tour_service
from app.core.exceptions import NotFoundException

router = APIRouter(prefix="/custom-tours", tags=["custom-tours"])


@router.get("/base-services", response_model=BaseServiceListResponse)
async def list_base_services(
    category: str | None = None,
    locale: str = Query("en"),
    db: AsyncSession = Depends(get_db),
):
    """获取所有可用基础服务列表。"""
    filters = {"status": "active"}
    if category:
        filters["category"] = category

    services = await crud_base_service.get_multi(
        db,
        filters=filters,
        order_by=crud_base_service.model.sort_order.asc(),
    )
    return BaseServiceListResponse(
        services=[
            BaseServiceResponse(
                id=s.id,
                name=s.name,
                name_zh=s.name_zh,
                name_es=s.name_es,
                name_fr=s.name_fr,
                description=s.description,
                description_zh=s.description_zh,
                description_es=s.description_es,
                description_fr=s.description_fr,
                unit_type=s.unit_type,
                unit_price=s.unit_price,
                currency=s.currency or "USD",
                category=s.category,
                sort_order=s.sort_order or 0,
                status=s.status,
            )
            for s in services
        ],
        total=len(services),
    )


@router.post("/quote", response_model=CustomTourQuoteResponse)
async def get_quote(
    req: CustomTourCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """获取自定制旅程报价（自动计算，不保存）。"""
    subtotal, breakdown = await custom_tour_service.calculate_quote(db, req)
    total_days = breakdown.get("total_days", 0)
    return CustomTourQuoteResponse(
        subtotal=subtotal,
        currency="USD",
        breakdown={
            "services": breakdown.get("services", 0),
            "pax_count": req.pax_count,
            "total_days": total_days,
            "segment_count": len(req.segments),
        },
    )


@router.post("/requests", status_code=201)
async def submit_custom_tour_request(
    req: CustomTourCreateRequest,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """提交自定制旅程需求（支持多段行程）。"""
    created = await custom_tour_service.submit_request(db, req, user)
    # 重查询完整关系（避免 async lazy loading MissingGreenlet）
    from app.crud.custom_tour import crud_custom_tour_request as crud_ct
    loaded = await crud_ct.get_with_relations(db, created.id)
    if not loaded:
        loaded = created
    response = await custom_tour_service.build_response(db, loaded)
    return {"status": "ok", "request": response}


@router.get("/requests", response_model=CustomTourRequestListResponse)
async def list_my_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的自定制旅程请求列表。"""
    if not user:
        return CustomTourRequestListResponse(requests=[], total=0, page=page, page_size=page_size)

    skip = (page - 1) * page_size
    requests = await crud_custom_tour_request.list_by_user(db, user.id, skip=skip, limit=page_size)
    total = await crud_custom_tour_request.count(db, filters={"user_id": user.id})

    responses = []
    for r in requests:
        r_with_rels = await crud_custom_tour_request.get_with_relations(db, r.id)
        if r_with_rels:
            responses.append(await custom_tour_service.build_response(db, r_with_rels))

    return CustomTourRequestListResponse(requests=responses, total=total, page=page, page_size=page_size)


@router.get("/requests/{request_id}", response_model=CustomTourRequestResponse)
async def get_request_detail(
    request_id: uuid.UUID,
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """获取自定制旅程请求详情。"""
    request = await crud_custom_tour_request.get_with_relations(db, request_id)
    if not request:
        raise NotFoundException(detail="Custom tour request not found")

    if user and (user.id == request.user_id or user.is_admin):
        return await custom_tour_service.build_response(db, request)
    raise HTTPException(status_code=403, detail="Not authorized to view this request")
