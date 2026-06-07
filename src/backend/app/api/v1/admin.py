"""管理后台 API。"""

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.api.dependencies import get_current_admin_user
from app.models.user import User
from app.models.tour import Tour, TourTranslation, TourDate, TourImage
from app.models.order import Order, OrderPassenger
from app.models.review import Review
from app.models.attraction import Attraction, AttractionTranslation
from app.models.attraction_media import AttractionMedia
from app.models.destination import Destination, DestinationTranslation
from app.models.custom_tour import BaseService, CustomTourRequest, CustomTourSegment, CustomTourSegmentTour, CustomTourAttraction, CustomTourService
from app.crud.tour import crud_tour, crud_tour_date
from app.schemas.tour import TourResponse, TourListResponse
from app.schemas.order import OrderResponse, OrderListResponse
from app.core.exceptions import NotFoundException, ConflictException, ValidationException
from app.config import settings
import shutil
from pathlib import Path


# ── Tour 创建请求 Schema ─────────────────────────────────────────────────

class TourTranslationCreate(BaseModel):
    locale: str
    name: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    itinerary: Optional[list[dict]] = None
    highlights: Optional[list[str]] = None
    includes: Optional[list[str]] = None
    excludes: Optional[list[str]] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class TourImageCreate(BaseModel):
    url: str
    alt_text: Optional[str] = None
    sort_order: int = 0
    type: str = "image"


class TourDateCreate(BaseModel):
    start_date: date
    end_date: date
    price_per_pax: float
    currency: str = "USD"
    availability: int = 0


class TourCreateRequest(BaseModel):
    slug: str
    status: str = "draft"
    type: str = "group_tour"
    sort_order: int = 0
    serial_number: Optional[str] = None
    duration_days: int
    duration_nights: int = 0
    max_pax: Optional[int] = None
    min_pax: int = 1
    start_price: float = 0
    currency: str = "USD"
    difficulty: str = "easy"
    theme: str = "citywalk"
    highlights: list[str] = []
    includes: list[str] = []
    excludes: list[str] = []
    destination_ids: list[uuid.UUID] = []
    translations: list[TourTranslationCreate] = []
    images: list[TourImageCreate] = []
    dates: list[TourDateCreate] = []

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================
# Dashboard Stats
# ============================================================

@router.get("/stats")
async def get_stats(
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取仪表盘统计数据。"""
    # 用户总数
    user_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    # 产品总数（含草稿）
    tour_count = (await db.execute(
        select(func.count(Tour.id)).where(Tour.deleted_at.is_(None))
    )).scalar() or 0
    # 已发布产品数
    published_count = (await db.execute(
        select(func.count(Tour.id)).where(
            Tour.status == "published", Tour.deleted_at.is_(None)
        )
    )).scalar() or 0
    # 订单总数
    order_count = (await db.execute(
        select(func.count(Order.id))
    )).scalar() or 0
    # 总收入（已支付）
    total_revenue = (await db.execute(
        select(func.sum(Order.total)).where(
            Order.payment_status == "paid"
        )
    )).scalar() or 0.0
    # 待处理评论
    pending_reviews = (await db.execute(
        select(func.count(Review.id)).where(Review.status == "pending")
    )).scalar() or 0

    return {
        "total_users": user_count,
        "total_tours": tour_count,
        "published_tours": published_count,
        "total_orders": order_count,
        "total_revenue": float(total_revenue),
        "pending_reviews": pending_reviews,
    }


# ============================================================
# Tours Management
# ============================================================

@router.get("/tours", response_model=TourListResponse)
async def admin_list_tours(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = select(Tour).options(
        selectinload(Tour.tour_translations),
        selectinload(Tour.tour_images),
    ).where(Tour.deleted_at.is_(None))

    if status:
        query = query.where(Tour.status == status)
    query = query.order_by(Tour.sort_order.asc().nullslast(), Tour.updated_at.desc()).offset(skip).limit(page_size)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query)
    tours = result.scalars().all()

    # Build response using existing service pattern
    from app.services.tour_service import tour_service
    tour_responses = [await tour_service._build_response(t, "en", db) for t in tours]

    return TourListResponse(tours=tour_responses, total=total, page=page, page_size=page_size)


@router.post("/tours", status_code=201)
async def admin_create_tour(
    body: TourCreateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新的旅游产品（含翻译、图片、团期）。"""
    # 检查 slug 唯一性
    existing = await db.execute(
        select(Tour).where(Tour.slug == body.slug, Tour.deleted_at.is_(None))
    )
    if existing.scalar_one_or_none():
        raise ConflictException(detail=f"Tour with slug '{body.slug}' already exists")

    # 自动生成序列号（若未提供）
    serial_number = body.serial_number
    if not serial_number and body.destination_ids:
        first_dest_id = body.destination_ids[0]
        sn_result = await db.execute(
            select(Tour.serial_number).where(
                Tour.destination_ids.any(first_dest_id),
                Tour.deleted_at.is_(None),
                Tour.serial_number.isnot(None),
            )
        )
        existing_sns = sn_result.scalars().all()
        max_num = max((int(sn) for sn in existing_sns if sn and sn.isdigit()), default=0)
        serial_number = str(max_num + 1).zfill(4)

    # 创建主产品
    tour = Tour(
        id=uuid.uuid4(),
        slug=body.slug,
        status=body.status,
        type=body.type,
        sort_order=body.sort_order,
        serial_number=serial_number,
        duration_days=body.duration_days,
        duration_nights=body.duration_nights,
        max_pax=body.max_pax,
        min_pax=body.min_pax,
        start_price=body.start_price,
        currency=body.currency,
        difficulty=body.difficulty,
        theme=body.theme or "citywalk",
        highlights=body.highlights or [],
        includes=body.includes or [],
        excludes=body.excludes or [],
        destination_ids=body.destination_ids or [],
        avg_rating=0.0,
        review_count=0,
        published_at=datetime.now(timezone.utc) if body.status == "published" else None,
    )
    db.add(tour)
    await db.flush()

    # 创建多语言翻译
    for trans in body.translations:
        translation = TourTranslation(
            id=uuid.uuid4(),
            tour_id=tour.id,
            locale=trans.locale,
            name=trans.name,
            subtitle=trans.subtitle,
            description=trans.description,
            itinerary=trans.itinerary,
            highlights=trans.highlights,
            includes=trans.includes,
            excludes=trans.excludes,
            meta_title=trans.meta_title,
            meta_description=trans.meta_description,
        )
        db.add(translation)

    # 创建图片
    for img in body.images:
        image = TourImage(
            id=uuid.uuid4(),
            tour_id=tour.id,
            url=img.url,
            alt_text=img.alt_text,
            sort_order=img.sort_order,
        )
        db.add(image)

    # 创建团期
    for dt in body.dates:
        tour_date = TourDate(
            id=uuid.uuid4(),
            tour_id=tour.id,
            start_date=dt.start_date,
            end_date=dt.end_date,
            price_per_pax=dt.price_per_pax,
            currency=dt.currency,
            availability=dt.availability,
            status="available",
        )
        db.add(tour_date)

    await db.flush()

    # 重新查询完整 tour（含关系），避免 async lazy loading 问题
    await db.refresh(tour)
    # 手动加载关联数据
    tour.tour_translations = (
        await db.execute(
            select(TourTranslation).where(TourTranslation.tour_id == tour.id)
        )
    ).scalars().all()
    tour.tour_images = (
        await db.execute(
            select(TourImage).where(TourImage.tour_id == tour.id).order_by(TourImage.sort_order)
        )
    ).scalars().all()
    tour.tour_dates = (
        await db.execute(
            select(TourDate).where(TourDate.tour_id == tour.id).order_by(TourDate.start_date)
        )
    ).scalars().all()

    # 构建返回结果
    from app.services.tour_service import tour_service
    response = await tour_service._build_response(tour, body.translations[0].locale if body.translations else "en", db)

    return {
        "status": "ok",
        "id": str(tour.id),
        "tour": response,
    }


# ── 图片上传 ─────────────────────────────────────────────────────────────

UPLOAD_DIR = Path(settings.static_dir) / "uploads" / "tours"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", tags=["admin"])
async def admin_upload_image(
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin_user),
):
    """上传旅游产品图片或短视频（≤60MB），返回可访问的 URL。"""
    # 校验文件类型
    IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
    VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"}
    allowed_types = IMAGE_TYPES | VIDEO_TYPES

    if file.content_type and file.content_type not in allowed_types:
        raise ValidationException(
            detail=f"Unsupported file type: {file.content_type}. "
                  f"Allowed: images (jpg/png/webp/gif/svg) and videos (mp4/webm/mov/avi)"
        )

    # 判断文件类型
    is_video = file.content_type in VIDEO_TYPES if file.content_type else False
    file_ext = Path(file.filename or ("video.mp4" if is_video else "image.jpg")).suffix

    # 限制视频大小 60MB
    MAX_SIZE = 60 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise ValidationException(detail=f"File too large ({len(content)/1024/1024:.1f}MB). Max: 60MB")

    # 生成唯一文件名并保存
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_name
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        raise ValidationException(detail=f"Failed to save file: {str(e)}")

    media_url = f"/static/uploads/tours/{unique_name}"
    return {"url": media_url, "filename": unique_name, "type": "video" if is_video else "image"}


@router.delete("/tours/{tour_id}/images/{image_id}")
async def admin_delete_tour_image(
    tour_id: uuid.UUID,
    image_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除产品图片/视频记录。"""
    from sqlalchemy import select, delete as sa_delete
    result = await db.execute(
        select(TourImage).where(TourImage.id == image_id, TourImage.tour_id == tour_id)
    )
    img = result.scalar_one_or_none()
    if not img:
        raise NotFoundException(detail="Image not found")
    await db.delete(img)
    await db.flush()
    return {"status": "deleted", "id": str(image_id)}


@router.patch("/tours/{tour_id}")
async def admin_update_tour(
    tour_id: uuid.UUID,
    body: dict,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新产品基础字段及翻译（支持单 locale 向后兼容 + 多 locale 批量更新）。"""
    tour = await crud_tour.get(db, tour_id)
    if not tour:
        raise NotFoundException(detail="Tour not found")

    # ── 翻译字段集合 ──────────────────────────────
    translation_fields = {"name", "subtitle", "description", "highlights", "includes", "excludes"}

    # ── 批量多语言更新（translations 数组） ─────────
    translations_list = body.get("translations")
    if translations_list is not None:
        for trans_data in translations_list:
            locale = trans_data.get("locale", "en")
            result = await db.execute(
                select(TourTranslation).where(
                    TourTranslation.tour_id == tour_id,
                    TourTranslation.locale == locale,
                )
            )
            trans = result.scalar_one_or_none()
            update_fields = {k: v for k, v in trans_data.items() if k in translation_fields and v is not None}
            if trans:
                for field, value in update_fields.items():
                    setattr(trans, field, value)
            elif update_fields:
                # 创建新翻译（name 为空时回退到 tour.slug）
                new_trans = TourTranslation(
                    id=uuid.uuid4(),
                    tour_id=tour_id,
                    locale=locale,
                    name=update_fields.get("name") or tour.slug,
                    subtitle=update_fields.get("subtitle"),
                    description=update_fields.get("description"),
                    highlights=update_fields.get("highlights"),
                    includes=update_fields.get("includes"),
                    excludes=update_fields.get("excludes"),
                )
                db.add(new_trans)

    # ── 单 locale 翻译更新（向后兼容） ────────────
    single_translation_data = {k: v for k, v in body.items() if k in translation_fields and v is not None}
    if single_translation_data and translations_list is None:
        locale = body.get("locale", "en")
        result = await db.execute(
            select(TourTranslation).where(
                TourTranslation.tour_id == tour_id,
                TourTranslation.locale == locale,
            )
        )
        trans = result.scalar_one_or_none()
        if trans:
            for field, value in single_translation_data.items():
                setattr(trans, field, value)
        else:
            new_trans = TourTranslation(
                id=uuid.uuid4(),
                tour_id=tour_id,
                locale=locale,
                name=single_translation_data.get("name", tour.slug),
                subtitle=single_translation_data.get("subtitle"),
                description=single_translation_data.get("description"),
                highlights=single_translation_data.get("highlights"),
                includes=single_translation_data.get("includes"),
                excludes=single_translation_data.get("excludes"),
            )
            db.add(new_trans)

    # ── 产品基础字段更新 ──────────────────────────
    exclude_keys = translation_fields | {"locale", "translations"}
    tour_fields = {k: v for k, v in body.items() if k not in exclude_keys}
    if tour_fields:
        await crud_tour.update(db, db_obj=tour, update_data=tour_fields)

    await db.flush()
    await db.refresh(tour)
    return {"status": "ok", "id": str(tour.id)}


@router.get("/tours/{tour_id}", response_model=TourResponse)
async def admin_get_tour(
    tour_id: uuid.UUID,
    locale: str = Query("en"),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取完整产品详情（含翻译、图片、团期），供编辑表单使用。"""
    from app.services.tour_service import tour_service
    from app.crud.tour import crud_tour

    tour = await crud_tour.get_with_details(db, tour_id, locale)
    if not tour:
        raise NotFoundException(detail="Tour not found")
    return await tour_service._build_response(tour, locale, db)


class TourFullUpdateRequest(BaseModel):
    """产品完整更新请求（与创建一致，所有字段可选）。"""
    slug: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    sort_order: Optional[int] = None
    serial_number: Optional[str] = None
    duration_days: Optional[int] = None
    duration_nights: Optional[int] = 0
    max_pax: Optional[int] = None
    min_pax: Optional[int] = None
    start_price: Optional[float] = None
    currency: Optional[str] = None
    difficulty: Optional[str] = None
    theme: Optional[str] = None
    highlights: Optional[list[str]] = None
    includes: Optional[list[str]] = None
    excludes: Optional[list[str]] = None
    translations: Optional[list[TourTranslationCreate]] = None
    images: Optional[list[TourImageCreate]] = None
    dates: Optional[list[TourDateCreate]] = None


@router.put("/tours/{tour_id}")
async def admin_full_update_tour(
    tour_id: uuid.UUID,
    body: TourFullUpdateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """完整更新产品信息（含翻译、图片、团期），替换式更新。"""
    tour = await crud_tour.get(db, tour_id)
    if not tour:
        raise NotFoundException(detail="Tour not found")

    # 1. 更新产品基础字段
    update_data = body.model_dump(exclude_none=True, exclude={"translations", "images", "dates"})
    if update_data:
        await crud_tour.update(db, db_obj=tour, update_data=update_data)

    # 2. 替换翻译（删旧加新）
    if body.translations is not None:
        await db.execute(
            sa_delete(TourTranslation).where(TourTranslation.tour_id == tour_id)
        )
        for trans in body.translations:
            db.add(TourTranslation(
                id=uuid.uuid4(),
                tour_id=tour_id,
                locale=trans.locale,
                name=trans.name,
                subtitle=trans.subtitle,
                description=trans.description,
                itinerary=trans.itinerary,
                highlights=trans.highlights,
                includes=trans.includes,
                excludes=trans.excludes,
                meta_title=trans.meta_title,
                meta_description=trans.meta_description,
            ))

    # 3. 替换图片（删旧加新）
    if body.images is not None:
        await db.execute(
            sa_delete(TourImage).where(TourImage.tour_id == tour_id)
        )
        for idx, img in enumerate(body.images):
            db.add(TourImage(
                id=uuid.uuid4(),
                tour_id=tour_id,
                url=img.url,
                alt_text=img.alt_text,
                sort_order=img.sort_order or idx + 1,
            ))

    # 4. 替换团期（删旧加新）
    if body.dates is not None:
        await db.execute(
            sa_delete(TourDate).where(TourDate.tour_id == tour_id)
        )
        for dt in body.dates:
            db.add(TourDate(
                id=uuid.uuid4(),
                tour_id=tour_id,
                start_date=dt.start_date,
                end_date=dt.end_date,
                price_per_pax=dt.price_per_pax,
                currency=dt.currency,
                availability=dt.availability,
                status="available",
            ))

    await db.flush()

    # 重建返回
    await db.refresh(tour)
    tour.tour_translations = (await db.execute(
        select(TourTranslation).where(TourTranslation.tour_id == tour_id)
    )).scalars().all()
    tour.tour_images = (await db.execute(
        select(TourImage).where(TourImage.tour_id == tour_id).order_by(TourImage.sort_order)
    )).scalars().all()
    tour.tour_dates = (await db.execute(
        select(TourDate).where(TourDate.tour_id == tour_id).order_by(TourDate.start_date)
    )).scalars().all()

    from app.services.tour_service import tour_service
    locale = body.translations[0].locale if body.translations else "en"
    response = await tour_service._build_response(tour, locale, db)

    return {"status": "ok", "id": str(tour.id), "tour": response}


@router.delete("/tours/{tour_id}")
async def admin_delete_tour(
    tour_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    tour = await crud_tour.get(db, tour_id)
    if not tour:
        raise NotFoundException(detail="Tour not found")
    # 软删除
    await crud_tour.update(db, db_obj=tour, update_data={"deleted_at": datetime.now(timezone.utc)})
    return {"status": "deleted"}


# ============================================================
# Tour Date Management
# ============================================================

class TourDateUpdateRequest(BaseModel):
    """团期更新请求（全部可选，只更新传了的字段）。"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    price_per_pax: Optional[float] = None
    availability: Optional[int] = None
    status: Optional[str] = None


@router.get("/tours/{tour_id}/dates")
async def admin_list_tour_dates(
    tour_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取产品所有团期（按日期排序）。"""
    dates = await crud_tour_date.get_by_tour(db, tour_id)
    return {
        "dates": [
            {
                "id": str(d.id),
                "tour_id": str(d.tour_id),
                "start_date": d.start_date.isoformat(),
                "end_date": d.end_date.isoformat(),
                "price_per_pax": d.price_per_pax,
                "currency": d.currency,
                "availability": d.availability,
                "status": d.status,
            }
            for d in dates
        ],
        "total": len(dates),
    }


@router.post("/tours/{tour_id}/dates", status_code=201)
async def admin_add_tour_date(
    tour_id: uuid.UUID,
    body: TourDateCreate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """为产品新增一个团期（即改即生效）。"""
    tour = await crud_tour.get(db, tour_id)
    if not tour:
        raise NotFoundException(detail="Tour not found")

    tour_date = TourDate(
        id=uuid.uuid4(),
        tour_id=tour_id,
        start_date=body.start_date,
        end_date=body.end_date,
        price_per_pax=body.price_per_pax,
        currency=body.currency,
        availability=body.availability,
        status="available",
    )
    db.add(tour_date)
    await db.flush()

    return {
        "status": "created",
        "id": str(tour_date.id),
        "start_date": tour_date.start_date.isoformat(),
        "price_per_pax": tour_date.price_per_pax,
        "availability": tour_date.availability,
    }


@router.patch("/tours/{tour_id}/dates/{date_id}")
async def admin_update_tour_date(
    tour_id: uuid.UUID,
    date_id: uuid.UUID,
    body: TourDateUpdateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新单个团期信息（价格、库存、状态等），即改即生效。"""
    tour_date = await crud_tour_date.get(db, date_id)
    if not tour_date or tour_date.tour_id != tour_id:
        raise NotFoundException(detail="Tour date not found")

    update_data = body.model_dump(exclude_none=True)
    if update_data:
        await crud_tour_date.update(db, db_obj=tour_date, update_data=update_data)

    return {
        "status": "ok",
        "id": str(date_id),
        "start_date": tour_date.start_date.isoformat(),
        "price_per_pax": tour_date.price_per_pax,
        "availability": tour_date.availability,
        "status": tour_date.status,
    }


@router.delete("/tours/{tour_id}/dates/{date_id}")
async def admin_delete_tour_date(
    tour_id: uuid.UUID,
    date_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除团期。"""
    tour_date = await crud_tour_date.get(db, date_id)
    if not tour_date or tour_date.tour_id != tour_id:
        raise NotFoundException(detail="Tour date not found")

    await db.delete(tour_date)
    await db.flush()

    return {"status": "deleted", "id": str(date_id)}


# ============================================================
# Orders Management
# ============================================================

@router.get("/orders")
async def admin_list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = select(Order).order_by(Order.created_at.desc())

    if status:
        query = query.where(Order.status == status)
    query = query.offset(skip).limit(page_size)

    total = (await db.execute(
        select(func.count(Order.id))
    )).scalar() or 0

    result = await db.execute(query)
    orders = result.scalars().all()

    return {
        "orders": [
            {
                "id": str(o.id),
                "order_no": o.order_no,
                "user_id": str(o.user_id) if o.user_id else None,
                "tour_id": str(o.tour_id),
                "status": o.status,
                "pax_count": o.pax_count,
                "total": o.total,
                "currency": o.currency or "USD",
                "payment_status": o.payment_status,
                "contact_name": o.contact_name,
                "contact_email": o.contact_email,
                "created_at": o.created_at.isoformat() if o.created_at else "",
            }
            for o in orders
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/orders/{order_id}/status")
async def admin_update_order_status(
    order_id: uuid.UUID,
    body: dict,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise NotFoundException(detail="Order not found")

    new_status = body.get("status")
    if new_status:
        order.status = new_status
    if body.get("payment_status"):
        order.payment_status = body["payment_status"]
    await db.flush()
    return {"status": "ok", "order_id": str(order.id), "new_status": order.status}


# ============================================================
# Users Management
# ============================================================

@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = select(User).order_by(User.created_at.desc()).offset(skip).limit(page_size)
    total = (await db.execute(select(func.count(User.id)))).scalar() or 0
    result = await db.execute(query)
    users = result.scalars().all()

    return {
        "users": [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "is_admin": u.is_admin or False,
                "is_active": u.is_active or True,
                "locale": u.locale or "en",
                "created_at": u.created_at.isoformat() if u.created_at else "",
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ============================================================
# Reviews Moderation
# ============================================================

@router.get("/reviews")
async def admin_list_reviews(
    status: str | None = "pending",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    query = select(Review).order_by(Review.created_at.desc())
    count_query = select(func.count(Review.id))

    if status:
        query = query.where(Review.status == status)
        count_query = count_query.where(Review.status == status)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    reviews = result.scalars().all()

    return {
        "reviews": [
            {
                "id": str(r.id),
                "tour_id": str(r.tour_id),
                "user_id": str(r.user_id),
                "rating": r.rating,
                "title": r.title,
                "comment": r.comment,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in reviews
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch("/reviews/{review_id}")
async def admin_update_review(
    review_id: uuid.UUID,
    body: dict,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundException(detail="Review not found")

    if body.get("status") in ("approved", "rejected"):
        review.status = body["status"]
        await db.flush()

    return {"status": "ok", "review_id": str(review.id), "new_status": review.status}


@router.post("/reindex")
async def admin_reindex_search(
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """手动重建 ES 搜索索引（同步执行 — 实时索引所有已发布产品）。"""
    try:
        from app.search.client import get_es, check_es_health
        from app.search.index import delete_index, create_index, bulk_index_tours

        if not await check_es_health():
            return {"status": "error", "detail": "Elasticsearch is not available"}
        es = await get_es()
        await delete_index(es)
        await create_index(es)
        count = await bulk_index_tours(db, es)
        return {
            "status": "ok",
            "detail": "Search index rebuilt successfully",
            "indexed_documents": count,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ============================================================
# Attractions Management
# ============================================================


@router.get("/attractions")
async def admin_list_attractions(
    destination_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有景点列表（含目的地名称、媒体数量）。"""
    skip = (page - 1) * page_size

    # Base query — join destinations for name
    query = (
        select(
            Attraction.id,
            Attraction.slug,
            Attraction.image_url,
            Attraction.sort_order,
            Attraction.rating,
            Attraction.status,
            Attraction.destination_id,
            DestinationTranslation.name.label("destination_name"),
            select(func.count(AttractionMedia.id))
            .where(AttractionMedia.attraction_id == Attraction.id)
            .correlate(Attraction)
            .scalar_subquery()
            .label("media_count"),
        )
        .select_from(Attraction)
        .outerjoin(Destination, Destination.id == Attraction.destination_id)
        .outerjoin(
            DestinationTranslation,
            (DestinationTranslation.destination_id == Destination.id)
            & (DestinationTranslation.locale == "en"),
        )
    )

    count_query = select(func.count(Attraction.id)).select_from(Attraction)

    if destination_id:
        query = query.where(Attraction.destination_id == destination_id)
        count_query = count_query.where(Attraction.destination_id == destination_id)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(DestinationTranslation.name, Attraction.sort_order).offset(skip).limit(page_size))
    rows = result.fetchall()

    return {
        "attractions": [
            {
                "id": str(r.id),
                "slug": r.slug,
                "image_url": r.image_url,
                "sort_order": r.sort_order or 0,
                "rating": r.rating or 0,
                "status": r.status or "active",
                "destination_id": str(r.destination_id),
                "destination_name": r.destination_name or "",
                "media_count": r.media_count or 0,
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/attractions/{attraction_id}")
async def admin_get_attraction(
    attraction_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取景点完整详情（含所有翻译、门票、媒体）。"""
    result = await db.execute(
        select(Attraction)
        .options(
            selectinload(Attraction.translations),
            selectinload(Attraction.tickets),
            selectinload(Attraction.media),
        )
        .where(Attraction.id == attraction_id)
    )
    attr = result.scalar_one_or_none()
    if not attr:
        raise NotFoundException(detail="Attraction not found")

    return {
        "id": str(attr.id),
        "slug": attr.slug,
        "destination_id": str(attr.destination_id),
        "image_url": attr.image_url,
        "sort_order": attr.sort_order or 0,
        "rating": attr.rating or 0,
        "status": attr.status or "active",
        "ticket_price": attr.ticket_price or 0,
        "ticket_currency": attr.ticket_currency or "USD",
        "translations": [
            {
                "id": str(t.id),
                "locale": t.locale,
                "name": t.name,
                "description": t.description,
                "ticket_info": t.ticket_info,
                "opening_hours": t.opening_hours,
                "meta_title": t.meta_title,
                "meta_description": t.meta_description,
            }
            for t in (attr.translations or [])
        ],
        "tickets": [
            {
                "id": str(t.id),
                "ticket_type": t.ticket_type,
                "price": t.price,
                "currency": t.currency,
                "availability": t.availability,
                "status": t.status,
            }
            for t in (attr.tickets or [])
        ],
        "media": sorted(
            [
                {
                    "id": str(m.id),
                    "url": m.url,
                    "media_type": m.media_type,
                    "alt_text": m.alt_text,
                    "sort_order": m.sort_order or 0,
                }
                for m in (attr.media or [])
            ],
            key=lambda x: x["sort_order"],
        ),
    }


@router.patch("/attractions/{attraction_id}")
async def admin_update_attraction(
    attraction_id: uuid.UUID,
    body: dict,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新景点基础信息及翻译。"""
    result = await db.execute(
        select(Attraction)
        .options(selectinload(Attraction.translations))
        .where(Attraction.id == attraction_id)
    )
    attr = result.scalar_one_or_none()
    if not attr:
        raise NotFoundException(detail="Attraction not found")

    # 基础字段更新
    basic_fields = {"image_url", "sort_order", "rating", "status", "ticket_price", "ticket_currency"}
    for key in basic_fields:
        if key in body and body[key] is not None:
            setattr(attr, key, body[key])

    # 翻译字段更新
    if body.get("translations"):
        # 获取已存在的翻译 locale -> obj map
        existing = {t.locale: t for t in (attr.translations or [])}
        for trans_data in body["translations"]:
            locale = trans_data.get("locale")
            if not locale:
                continue
            if locale in existing:
                t = existing[locale]
                for tf in ("name", "description", "ticket_info", "opening_hours", "meta_title", "meta_description"):
                    if tf in trans_data and trans_data[tf] is not None:
                        setattr(t, tf, trans_data[tf])
            else:
                # 创建新翻译（通常不应发生，但要兼容）
                new_t = AttractionTranslation(
                    attraction_id=attr.id,
                    locale=locale,
                    name=trans_data.get("name", ""),
                    description=trans_data.get("description"),
                )
                db.add(new_t)

    await db.flush()
    return {"status": "ok", "id": str(attr.id)}


@router.post("/attractions/{attraction_id}/media")
async def admin_add_attraction_media(
    attraction_id: uuid.UUID,
    body: dict,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """为景点添加媒体资源（照片/短视频 URL）。"""
    result = await db.execute(select(Attraction).where(Attraction.id == attraction_id))
    attr = result.scalar_one_or_none()
    if not attr:
        raise NotFoundException(detail="Attraction not found")

    # 计算当前 media 数量（限 8 个）
    count_result = await db.execute(
        select(func.count(AttractionMedia.id)).where(AttractionMedia.attraction_id == attraction_id)
    )
    current_count = count_result.scalar() or 0
    if current_count >= 8:
        raise ValidationException(detail="Maximum 8 media items per attraction")

    # 获取当前最大 sort_order
    max_order = await db.execute(
        select(func.coalesce(func.max(AttractionMedia.sort_order), -1)).where(
            AttractionMedia.attraction_id == attraction_id
        )
    )
    next_order = (max_order.scalar() or -1) + 1

    media = AttractionMedia(
        attraction_id=attr.id,
        url=body["url"],
        media_type=body.get("media_type", "image"),
        alt_text=body.get("alt_text"),
        sort_order=next_order,
    )
    db.add(media)
    await db.flush()

    return {
        "status": "ok",
        "media": {
            "id": str(media.id),
            "url": media.url,
            "media_type": media.media_type,
            "alt_text": media.alt_text,
            "sort_order": media.sort_order or 0,
        },
    }


@router.delete("/attractions/{attraction_id}/media/{media_id}")
async def admin_delete_attraction_media(
    attraction_id: uuid.UUID,
    media_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除景点媒体资源。"""
    result = await db.execute(
        select(AttractionMedia).where(
            AttractionMedia.id == media_id, AttractionMedia.attraction_id == attraction_id
        )
    )
    media = result.scalar_one_or_none()
    if not media:
        raise NotFoundException(detail="Media not found")

    await db.delete(media)
    await db.flush()
    return {"status": "ok", "deleted": str(media_id)}


@router.put("/attractions/{attraction_id}/media/reorder")
async def admin_reorder_attraction_media(
    attraction_id: uuid.UUID,
    body: dict,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """重排景点媒体顺序。body: { \"order\": [\"media_id_1\", \"media_id_2\", ...] }"""
    order_list = body.get("order", [])
    for idx, media_id_str in enumerate(order_list):
        media_uuid = uuid.UUID(media_id_str)
        await db.execute(
            update(AttractionMedia)
            .where(
                AttractionMedia.id == media_uuid,
                AttractionMedia.attraction_id == attraction_id,
            )
            .values(sort_order=idx)
        )
    await db.flush()
    return {"status": "ok"}


# ============================================================
# Base Services Management (超管录入基础服务)
# ============================================================


class BaseServiceCreateRequest(BaseModel):
    """基础服务创建请求。"""
    name: str
    name_zh: Optional[str] = None
    name_es: Optional[str] = None
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_zh: Optional[str] = None
    description_es: Optional[str] = None
    description_fr: Optional[str] = None
    unit_type: str = "per_day"  # per_day / per_pax / per_trip
    unit_price: float = 0
    currency: str = "USD"
    category: Optional[str] = None
    sort_order: int = 0
    status: str = "active"


class BaseServiceUpdateRequest(BaseModel):
    """基础服务更新请求（全部可选）。"""
    name: Optional[str] = None
    name_zh: Optional[str] = None
    name_es: Optional[str] = None
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_zh: Optional[str] = None
    description_es: Optional[str] = None
    description_fr: Optional[str] = None
    unit_type: Optional[str] = None
    unit_price: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    sort_order: Optional[int] = None
    status: Optional[str] = None


# ============================================================
# Destinations Management
# ============================================================


class DestinationCreateRequest(BaseModel):
    """目的地创建请求。"""
    slug: str
    image_url: Optional[str] = None
    status: str = "active"
    translations: list[dict] = []  # [{locale, name, description, ...}]


class DestinationUpdateRequest(BaseModel):
    """目的地更新请求（全部可选）。"""
    slug: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None
    translations: Optional[list[dict]] = None


@router.get("/destinations")
async def admin_list_destinations(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有目的地列表（含 translations 数量）。"""
    skip = (page - 1) * page_size
    # Count
    count_query = select(func.count(Destination.id))
    total = (await db.execute(count_query)).scalar() or 0

    # Query
    query = (
        select(
            Destination.id,
            Destination.slug,
            Destination.image_url,
            Destination.status,
            Destination.created_at,
            select(func.count(DestinationTranslation.id))
            .where(DestinationTranslation.destination_id == Destination.id)
            .correlate(Destination)
            .scalar_subquery()
            .label("translation_count"),
        )
        .order_by(Destination.created_at.desc())
        .offset(skip)
        .limit(page_size)
    )
    result = await db.execute(query)
    rows = result.fetchall()

    return {
        "destinations": [
            {
                "id": str(r.id),
                "slug": r.slug,
                "image_url": r.image_url or "",
                "status": r.status or "active",
                "translation_count": r.translation_count or 0,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/destinations/{destination_id}")
async def admin_get_destination(
    destination_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取目的地完整详情（含所有翻译）。"""
    result = await db.execute(
        select(Destination)
        .options(selectinload(Destination.translations))
        .where(Destination.id == destination_id)
    )
    dest = result.scalar_one_or_none()
    if not dest:
        raise NotFoundException(detail="Destination not found")

    return {
        "id": str(dest.id),
        "slug": dest.slug,
        "image_url": dest.image_url or "",
        "status": dest.status or "active",
        "translations": [
            {
                "id": str(t.id),
                "locale": t.locale,
                "name": t.name,
                "description": t.description or "",
                "meta_title": t.meta_title or "",
                "meta_description": t.meta_description or "",
            }
            for t in (dest.translations or [])
        ],
        "created_at": dest.created_at.isoformat() if dest.created_at else "",
        "updated_at": dest.updated_at.isoformat() if dest.updated_at else "",
    }


@router.post("/destinations", status_code=201)
async def admin_create_destination(
    body: DestinationCreateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新目的地（含 translations）。"""
    # Check slug uniqueness
    existing = await db.execute(
        select(Destination).where(Destination.slug == body.slug)
    )
    if existing.scalar_one_or_none():
        raise ConflictException(detail=f"Destination with slug '{body.slug}' already exists")

    dest = Destination(
        id=uuid.uuid4(),
        slug=body.slug,
        image_url=body.image_url,
        status=body.status or "active",
    )
    db.add(dest)
    await db.flush()

    for trans_data in body.translations:
        translation = DestinationTranslation(
            id=uuid.uuid4(),
            destination_id=dest.id,
            locale=trans_data.get("locale", "en"),
            name=trans_data.get("name", dest.slug),
            description=trans_data.get("description"),
            meta_title=trans_data.get("meta_title"),
            meta_description=trans_data.get("meta_description"),
        )
        db.add(translation)

    await db.flush()
    return {"status": "ok", "id": str(dest.id)}


@router.put("/destinations/{destination_id}")
async def admin_update_destination(
    destination_id: uuid.UUID,
    body: DestinationUpdateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新目的地信息及翻译。"""
    result = await db.execute(
        select(Destination)
        .options(selectinload(Destination.translations))
        .where(Destination.id == destination_id)
    )
    dest = result.scalar_one_or_none()
    if not dest:
        raise NotFoundException(detail="Destination not found")

    # Basic fields
    if body.slug is not None:
        dest.slug = body.slug
    if body.image_url is not None:
        dest.image_url = body.image_url
    if body.status is not None:
        dest.status = body.status

    # Translations
    if body.translations is not None:
        existing = {t.locale: t for t in (dest.translations or [])}
        for trans_data in body.translations:
            locale = trans_data.get("locale", "en")
            if locale in existing:
                t = existing[locale]
                for field in ("name", "description", "meta_title", "meta_description"):
                    if field in trans_data and trans_data[field] is not None:
                        setattr(t, field, trans_data[field])
            else:
                new_t = DestinationTranslation(
                    id=uuid.uuid4(),
                    destination_id=dest.id,
                    locale=locale,
                    name=trans_data.get("name", dest.slug),
                    description=trans_data.get("description"),
                    meta_title=trans_data.get("meta_title"),
                    meta_description=trans_data.get("meta_description"),
                )
                db.add(new_t)

    await db.flush()
    return {"status": "ok", "id": str(dest.id)}


@router.delete("/destinations/{destination_id}")
async def admin_delete_destination(
    destination_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除目的地（先检查关联数据，手动级联删除翻译后删除目的地）。"""
    # 使用 lazyload 避免 selectin 加载 translations 导致 UPDATE NULL 冲突
    result = await db.execute(
        select(Destination).options(selectinload(Destination.translations)).where(Destination.id == destination_id)
    )
    dest = result.scalar_one_or_none()
    if not dest:
        raise NotFoundException(detail="Destination not found")

    # 检查是否有景点关联
    attr_result = await db.execute(
        select(func.count(Attraction.id)).where(Attraction.destination_id == destination_id)
    )
    attr_count = attr_result.scalar() or 0
    if attr_count > 0:
        raise ValidationException(
            detail=f"Cannot delete: {attr_count} attraction(s) are linked to this destination. Remove or reassign them first."
        )

    # 检查是否有行程段关联
    seg_result = await db.execute(
        select(func.count(CustomTourSegment.id)).where(CustomTourSegment.destination_id == destination_id)
    )
    seg_count = seg_result.scalar() or 0
    if seg_count > 0:
        raise ValidationException(
            detail=f"Cannot delete: {seg_count} custom tour segment(s) reference this destination."
        )

    # 手动删除翻译（避免 NOT NULL 冲突）
    await db.execute(
        sa_delete(DestinationTranslation).where(DestinationTranslation.destination_id == destination_id)
    )
    await db.delete(dest)
    await db.flush()
    return {"status": "deleted", "id": str(destination_id)}


@router.get("/base-services")
async def admin_list_base_services(
    category: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有基础服务列表。"""
    skip = (page - 1) * page_size
    query = select(BaseService)

    if category:
        query = query.where(BaseService.category == category)
    if status:
        query = query.where(BaseService.status == status)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(BaseService.sort_order.asc().nullslast(), BaseService.name.asc())
    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    services = result.scalars().all()

    return {
        "services": [
            {
                "id": str(s.id),
                "name": s.name,
                "name_zh": s.name_zh,
                "name_es": s.name_es,
                "name_fr": s.name_fr,
                "description": s.description,
                "description_zh": s.description_zh,
                "description_es": s.description_es,
                "description_fr": s.description_fr,
                "unit_type": s.unit_type,
                "unit_price": s.unit_price,
                "currency": s.currency or "USD",
                "category": s.category,
                "sort_order": s.sort_order or 0,
                "status": s.status or "active",
            }
            for s in services
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/base-services", status_code=201)
async def admin_create_base_service(
    body: BaseServiceCreateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """创建基础服务。"""
    service = BaseService(
        id=uuid.uuid4(),
        name=body.name,
        name_zh=body.name_zh,
        name_es=body.name_es,
        name_fr=body.name_fr,
        description=body.description,
        description_zh=body.description_zh,
        description_es=body.description_es,
        description_fr=body.description_fr,
        unit_type=body.unit_type,
        unit_price=body.unit_price,
        currency=body.currency,
        category=body.category,
        sort_order=body.sort_order,
        status=body.status,
    )
    db.add(service)
    await db.flush()
    return {
        "status": "ok",
        "id": str(service.id),
        "service": {
            "id": str(service.id),
            "name": service.name,
            "unit_type": service.unit_type,
            "unit_price": service.unit_price,
            "category": service.category,
        },
    }


@router.put("/base-services/{service_id}")
async def admin_update_base_service(
    service_id: uuid.UUID,
    body: BaseServiceUpdateRequest,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新基础服务。"""
    result = await db.execute(select(BaseService).where(BaseService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise NotFoundException(detail="Base service not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(service, field, value)
    await db.flush()

    return {"status": "ok", "id": str(service_id)}


@router.delete("/base-services/{service_id}")
async def admin_delete_base_service(
    service_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """删除基础服务。"""
    result = await db.execute(select(BaseService).where(BaseService.id == service_id))
    service = result.scalar_one_or_none()
    if not service:
        raise NotFoundException(detail="Base service not found")
    await db.delete(service)
    await db.flush()
    return {"status": "deleted", "id": str(service_id)}


# ============================================================
# Custom Tour Requests Management（支持多段行程）
# ============================================================


@router.get("/custom-tours")
async def admin_list_custom_tour_requests(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有自定制旅程请求（展示首段目的地信息）。"""
    skip = (page - 1) * page_size
    query = select(CustomTourRequest).order_by(CustomTourRequest.created_at.desc())

    if status:
        query = query.where(CustomTourRequest.status == status)

    total_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_query)).scalar() or 0

    query = query.offset(skip).limit(page_size)
    result = await db.execute(query)
    requests = result.scalars().all()

    request_list = []
    for r in requests:
        # 获取首段行程信息（用于列表展示）
        first_seg_result = await db.execute(
            select(CustomTourSegment)
            .where(CustomTourSegment.request_id == r.id)
            .order_by(CustomTourSegment.segment_order)
            .limit(1)
        )
        first_seg = first_seg_result.scalar_one_or_none()

        dest_name = ""
        seg_dest_id = first_seg.destination_id if first_seg else None
        seg_start = first_seg.start_date if first_seg else None
        seg_end = first_seg.end_date if first_seg else None

        if seg_dest_id:
            dest_result = await db.execute(
                select(DestinationTranslation).where(
                    DestinationTranslation.destination_id == seg_dest_id,
                    DestinationTranslation.locale == "en",
                )
            )
            dest_trans = dest_result.scalar_one_or_none()
            if dest_trans:
                dest_name = dest_trans.name
        elif first_seg and first_seg.custom_destination:
            dest_name = first_seg.custom_destination

        seg_count_result = await db.execute(
            select(func.count(CustomTourSegment.id))
            .where(CustomTourSegment.request_id == r.id)
        )
        seg_count = seg_count_result.scalar() or 0

        request_list.append({
            "id": str(r.id),
            "request_no": r.request_no,
            "destination_name": dest_name,
            "segment_count": seg_count,
            "start_date": seg_start.isoformat() if seg_start else "",
            "end_date": seg_end.isoformat() if seg_end else "",
            "pax_count": r.pax_count,
            "guide_language": r.guide_language,
            "contact_name": r.contact_name,
            "contact_email": r.contact_email,
            "contact_phone": r.contact_phone,
            "subtotal": r.subtotal or 0,
            "confirmed_price": r.confirmed_price,
            "currency": r.currency or "USD",
            "status": r.status,
            "user_id": str(r.user_id) if r.user_id else None,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        })

    return {
        "requests": request_list,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/custom-tours/{request_id}")
async def admin_get_custom_tour_request(
    request_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """获取自定制旅程请求详情（含多段行程、景点、产品、服务）。"""
    from app.services.custom_tour_service import custom_tour_service

    result = await db.execute(
        select(CustomTourRequest).where(CustomTourRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    if not request:
        raise NotFoundException(detail="Custom tour request not found")

    # 加载多段行程
    seg_result = await db.execute(
        select(CustomTourSegment)
        .where(CustomTourSegment.request_id == request_id)
        .order_by(CustomTourSegment.segment_order)
    )
    segments = seg_result.scalars().all()

    segments_data = []
    for seg in segments:
        # 目的地名称（优先系统目的地，其次自定义）
        dest_name = ""
        if seg.destination_id:
            dest_result = await db.execute(
                select(DestinationTranslation).where(
                    DestinationTranslation.destination_id == seg.destination_id,
                ).limit(1)
            )
            dest_trans = dest_result.scalars().first()
            if dest_trans:
                dest_name = dest_trans.name
        elif seg.custom_destination:
            dest_name = seg.custom_destination

        # 景点
        attr_result = await db.execute(
            select(CustomTourAttraction)
            .where(CustomTourAttraction.segment_id == seg.id)
            .order_by(CustomTourAttraction.sort_order)
        )
        attractions = attr_result.scalars().all()
        attr_data = []
        for a in attractions:
            attr_name = ""
            attr_trans_result = await db.execute(
                select(AttractionTranslation).where(
                    AttractionTranslation.attraction_id == a.attraction_id,
                ).limit(1)
            )
            attr_trans = attr_trans_result.scalars().first()
            if attr_trans:
                attr_name = attr_trans.name
            attr_data.append({
                "id": str(a.id),
                "attraction_id": str(a.attraction_id),
                "attraction_name": attr_name,
                "sort_order": a.sort_order or 0,
            })

        # 已有产品（多选）
        tour_result = await db.execute(
            select(CustomTourSegmentTour)
            .where(CustomTourSegmentTour.segment_id == seg.id)
        )
        selected_tours = tour_result.scalars().all()
        tour_data = []
        for t in selected_tours:
            tour_name = ""
            tt_result = await db.execute(
                select(TourTranslation).where(
                    TourTranslation.tour_id == t.tour_id,
                ).limit(1)
            )
            tt = tt_result.scalars().first()
            if tt:
                tour_name = tt.name
            tour_data.append({
                "id": str(t.id),
                "tour_id": str(t.tour_id),
                "tour_name": tour_name,
            })

        segments_data.append({
            "id": str(seg.id),
            "segment_order": seg.segment_order,
            "destination_id": str(seg.destination_id) if seg.destination_id else None,
            "destination_name": dest_name,
            "custom_destination": seg.custom_destination,
            "start_date": seg.start_date.isoformat(),
            "end_date": seg.end_date.isoformat(),
            "attractions": attr_data,
            "selected_tours": tour_data,
        })

    # 服务
    svc_result = await db.execute(
        select(CustomTourService)
        .where(CustomTourService.request_id == request_id)
    )
    services = svc_result.scalars().all()
    service_data = []
    for s in services:
        svc_name = ""
        bsvc_result = await db.execute(
            select(BaseService).where(BaseService.id == s.service_id)
        )
        base_svc = bsvc_result.scalar_one_or_none()
        if base_svc:
            svc_name = base_svc.name
        service_data.append({
            "id": str(s.id),
            "service_id": str(s.service_id),
            "service_name": svc_name,
            "unit_price_snapshot": s.unit_price_snapshot,
            "quantity": s.quantity,
            "subtotal": s.subtotal,
        })

    return {
        "id": str(request.id),
        "request_no": request.request_no,
        "user_id": str(request.user_id) if request.user_id else None,
        "pax_count": request.pax_count,
        "guide_language": request.guide_language,
        "contact_name": request.contact_name,
        "contact_email": request.contact_email,
        "contact_phone": request.contact_phone,
        "special_requests": request.special_requests,
        "subtotal": request.subtotal or 0,
        "confirmed_price": request.confirmed_price,
        "currency": request.currency or "USD",
        "status": request.status,
        "admin_notes": request.admin_notes,
        "locale": request.locale or "en",
        "segments": segments_data,
        "services": service_data,
        "created_at": request.created_at.isoformat() if request.created_at else "",
        "updated_at": request.updated_at.isoformat() if request.updated_at else "",
    }


@router.patch("/custom-tours/{request_id}")
async def admin_update_custom_tour_request(
    request_id: uuid.UUID,
    body: dict,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """更新自定制旅程请求（确认价格、状态、备注）。"""
    result = await db.execute(
        select(CustomTourRequest).where(CustomTourRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    if not request:
        raise NotFoundException(detail="Custom tour request not found")

    allowed_fields = {"status", "confirmed_price", "admin_notes"}
    for field in allowed_fields:
        if field in body and body[field] is not None:
            setattr(request, field, body[field])

    await db.flush()

    # 当状态变为 quoted 且已设置确认价格时，发送邮件通知客户
    if request.status == "quoted" and request.confirmed_price is not None:
        try:
            # 计算总天数
            from app.models.custom_tour import CustomTourSegment
            seg_result = await db.execute(
                select(CustomTourSegment)
                .where(CustomTourSegment.request_id == request.id)
            )
            segments = list(seg_result.scalars().all())
            total_days = sum(
                max(1, (seg.end_date - seg.start_date).days)
                for seg in segments
            ) if segments else 0

            # 异步发送邮件
            from app.tasks.email_tasks import send_custom_tour_notification
            send_custom_tour_notification.delay(
                user_email=request.contact_email,
                contact_name=request.contact_name,
                request_no=request.request_no,
                pax_count=request.pax_count,
                subtotal=request.subtotal or 0,
                confirmed_price=request.confirmed_price,
                currency=request.currency or "USD",
                segments_count=len(segments),
                total_days=total_days,
            )
        except Exception as e:
            # 邮件发送失败不应阻塞主流程
            import logging
            logging.getLogger(__name__).warning(f"Failed to trigger custom tour email: {e}")

    return {
        "status": "ok",
        "id": str(request.id),
        "new_status": request.status,
        "confirmed_price": request.confirmed_price,
    }


# ============================================================
# Enquiries Management
# ============================================================


@router.get("/enquiries")
async def admin_list_enquiries(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员：查询咨询列表。"""
    from app.models.enquiry import Enquiry

    filters = {}
    if status:
        filters["status"] = status
    skip = (page - 1) * page_size
    query = select(Enquiry)
    if status:
        query = query.where(Enquiry.status == status)
    query = query.order_by(Enquiry.created_at.desc()).offset(skip).limit(page_size)
    result = await db.execute(query)
    enquiries = list(result.scalars().all())
    count_query = select(func.count()).select_from(Enquiry)
    if status:
        count_query = count_query.where(Enquiry.status == status)
    total = (await db.execute(count_query)).scalar() or 0
    return {
        "enquiries": [{"id": str(e.id), "name": e.name, "email": e.email, "phone": e.phone, "destination": e.destination, "pax_count": e.pax_count, "message": e.message, "status": e.status, "admin_notes": e.admin_notes, "created_at": e.created_at.isoformat()} for e in enquiries],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/enquiries/{enquiry_id}")
async def admin_get_enquiry(
    enquiry_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员：获取咨询详情。"""
    from app.models.enquiry import Enquiry

    result = await db.execute(select(Enquiry).where(Enquiry.id == enquiry_id))
    enquiry = result.scalar_one_or_none()
    if not enquiry:
        raise NotFoundException(detail="Enquiry not found")
    return {
        "id": str(enquiry.id),
        "name": enquiry.name,
        "email": enquiry.email,
        "phone": enquiry.phone,
        "destination": enquiry.destination,
        "pax_count": enquiry.pax_count,
        "message": enquiry.message,
        "status": enquiry.status,
        "admin_notes": enquiry.admin_notes,
        "created_at": enquiry.created_at.isoformat(),
        "updated_at": enquiry.updated_at.isoformat() if enquiry.updated_at else None,
    }


@router.patch("/enquiries/{enquiry_id}")
async def admin_update_enquiry(
    enquiry_id: uuid.UUID,
    body: dict,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员：更新咨询状态/备注。"""
    from app.models.enquiry import Enquiry

    result = await db.execute(select(Enquiry).where(Enquiry.id == enquiry_id))
    enquiry = result.scalar_one_or_none()
    if not enquiry:
        raise NotFoundException(detail="Enquiry not found")
    allowed = {"status", "admin_notes"}
    for field in allowed:
        if field in body and body[field] is not None:
            setattr(enquiry, field, body[field])
    await db.flush()
    return {"status": "ok", "id": str(enquiry.id)}


@router.delete("/enquiries/{enquiry_id}")
async def admin_delete_enquiry(
    enquiry_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """管理员：删除咨询记录。"""
    from app.models.enquiry import Enquiry

    result = await db.execute(select(Enquiry).where(Enquiry.id == enquiry_id))
    enquiry = result.scalar_one_or_none()
    if not enquiry:
        raise NotFoundException(detail="Enquiry not found")
    await db.delete(enquiry)
    await db.flush()
    return {"status": "ok", "detail": "Enquiry deleted"}
