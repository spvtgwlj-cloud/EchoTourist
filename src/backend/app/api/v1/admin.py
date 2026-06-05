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
    duration_days: int
    duration_nights: int = 0
    max_pax: Optional[int] = None
    min_pax: int = 1
    start_price: float = 0
    currency: str = "USD"
    difficulty: str = "easy"
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
    query = query.order_by(Tour.updated_at.desc()).offset(skip).limit(page_size)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query)
    tours = result.scalars().all()

    # Build response using existing service pattern
    from app.services.tour_service import tour_service
    tour_responses = [await tour_service._build_response(t, "en") for t in tours]

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

    # 创建主产品
    tour = Tour(
        id=uuid.uuid4(),
        slug=body.slug,
        status=body.status,
        type=body.type,
        duration_days=body.duration_days,
        duration_nights=body.duration_nights,
        max_pax=body.max_pax,
        min_pax=body.min_pax,
        start_price=body.start_price,
        currency=body.currency,
        difficulty=body.difficulty,
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
    response = await tour_service._build_response(tour, body.translations[0].locale if body.translations else "en")

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
    return await tour_service._build_response(tour, locale)


class TourFullUpdateRequest(BaseModel):
    """产品完整更新请求（与创建一致，所有字段可选）。"""
    slug: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    duration_days: Optional[int] = None
    duration_nights: Optional[int] = 0
    max_pax: Optional[int] = None
    min_pax: Optional[int] = None
    start_price: Optional[float] = None
    currency: Optional[str] = None
    difficulty: Optional[str] = None
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
    response = await tour_service._build_response(tour, locale)

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
