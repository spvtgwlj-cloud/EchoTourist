"""订单业务逻辑服务。"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientStockException, NotFoundException, ValidationException
from app.crud.attraction_ticket import crud_attraction_ticket
from app.crud.order import crud_order
from app.crud.tour import crud_tour, crud_tour_date
from app.models.attraction import Attraction
from app.models.order import Order
from app.models.tour import TourDate, TourTranslation
from app.models.user import User
from app.schemas.order import BookingRequest, OrderListResponse, OrderResponse


class OrderService:
    @staticmethod
    def _generate_order_no() -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        suffix = str(uuid4())[:8].upper()
        return f"ECHO-{ts}-{suffix}"

    @staticmethod
    async def _load_tour_date_str(db: AsyncSession, tour_date_id: UUID | None) -> str:
        if not tour_date_id:
            return ""
        td_result = await db.execute(select(TourDate).where(TourDate.id == tour_date_id))
        td = td_result.scalar_one_or_none()
        return td.start_date.isoformat() if td and td.start_date else ""

    @staticmethod
    async def _invalidate_tour_dates_cache():
        """Invalidate tour dates cache so fresh data is returned."""
        try:
            from app.cache.client import get_redis
            redis = await get_redis()
            pattern = "cache:TourService.get_tour_dates:*"
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await redis.delete(*keys)
        except Exception:
            pass

    async def create_booking(
        self,
        db: AsyncSession,
        *,
        req: BookingRequest,
        user: User,
    ) -> OrderResponse:
        # Validate: must provide either (tour_id + tour_date_id) or (attraction_id + attraction_ticket_id)
        has_tour = bool(req.tour_id and req.tour_date_id)
        has_attraction = bool(req.attraction_id and req.attraction_ticket_id)
        if not has_tour and not has_attraction:
            raise ValidationException(
                detail="Must provide either (tour_id + tour_date_id) or (attraction_id + attraction_ticket_id)"
            )
        if has_tour and has_attraction:
            raise ValidationException(
                detail="Cannot provide both tour and attraction booking parameters"
            )

        if has_tour:
            return await self._create_tour_booking(db, req, user)
        return await self._create_attraction_booking(db, req, user)

    async def _create_tour_booking(
        self, db: AsyncSession, req: BookingRequest, user: User
    ) -> OrderResponse:
        tour = await crud_tour.get(db, req.tour_id)
        if not tour:
            raise NotFoundException(detail="Tour not found")

        tour_date = await crud_tour_date.decrement_availability(
            db, req.tour_date_id, req.pax_count
        )
        if not tour_date:
            td = await crud_tour_date.get(db, req.tour_date_id)
            if not td:
                raise NotFoundException(detail="Tour date not found")
            raise InsufficientStockException(
                detail=f"Only {td.availability} spots available"
            )

        # Get translation for tour_name
        trans_result = await db.execute(
            select(TourTranslation).where(
                TourTranslation.tour_id == req.tour_id,
                TourTranslation.locale == req.locale,
            )
        )
        translation = trans_result.scalar_one_or_none()

        total = tour_date.price_per_pax * req.pax_count
        order = Order(
            order_no=self._generate_order_no(),
            user_id=user.id,
            tour_id=req.tour_id,
            tour_date_id=req.tour_date_id,
            status="pending",
            pax_count=req.pax_count,
            subtotal=total,
            total=total,
            currency=tour_date.currency,
            contact_name=req.contact_name,
            contact_email=req.contact_email,
            contact_phone=req.contact_phone,
            special_requests=req.special_requests,
            locale=req.locale,
        )
        db.add(order)
        await db.flush()

        await self._invalidate_tour_dates_cache()

        return OrderResponse(
            id=order.id,
            order_no=order.order_no,
            tour_id=order.tour_id,
            tour_name=translation.name if translation else None,
            tour_date=tour_date.start_date.isoformat() if tour_date.start_date else "",
            status=order.status,
            pax_count=order.pax_count,
            total=order.total,
            currency=order.currency,
            contact_name=order.contact_name or "",
            contact_email=order.contact_email or "",
            created_at=order.created_at.isoformat() if order.created_at else "",
            payment_status=order.payment_status,
        )

    async def _create_attraction_booking(
        self, db: AsyncSession, req: BookingRequest, user: User
    ) -> OrderResponse:
        # Validate attraction exists
        attr_result = await db.execute(
            select(Attraction).where(
                Attraction.id == req.attraction_id,
                Attraction.status == "active",
            )
        )
        attr = attr_result.scalar_one_or_none()
        if not attr:
            raise NotFoundException(detail="Attraction not found")

        # Validate & atomically decrement ticket availability
        ticket = await crud_attraction_ticket.decrement_availability(
            db, req.attraction_ticket_id, req.pax_count
        )
        if not ticket:
            t = await crud_attraction_ticket.get(db, req.attraction_ticket_id)
            if not t:
                raise NotFoundException(detail="Attraction ticket not found")
            raise InsufficientStockException(
                detail=f"Only {t.availability} tickets available"
            )

        # Get attraction name from translation
        translation = None
        locale_fallback = None
        for t in (attr.translations or []):
            if t.locale == req.locale:
                translation = t
                break
            if t.locale == "en":
                locale_fallback = t
        if not translation:
            translation = locale_fallback or (attr.translations[0] if attr.translations else None)

        total = ticket.price * req.pax_count
        order = Order(
            order_no=self._generate_order_no(),
            user_id=user.id,
            attraction_id=req.attraction_id,
            attraction_ticket_id=req.attraction_ticket_id,
            status="pending",
            pax_count=req.pax_count,
            subtotal=total,
            total=total,
            currency=ticket.currency,
            contact_name=req.contact_name,
            contact_email=req.contact_email,
            contact_phone=req.contact_phone,
            special_requests=req.special_requests,
            locale=req.locale,
        )
        db.add(order)
        await db.flush()

        return OrderResponse(
            id=order.id,
            order_no=order.order_no,
            attraction_id=req.attraction_id,
            attraction_name=translation.name if translation else attr.slug,
            status=order.status,
            pax_count=order.pax_count,
            total=order.total,
            currency=order.currency or "USD",
            contact_name=order.contact_name or "",
            contact_email=order.contact_email or "",
            created_at=order.created_at.isoformat() if order.created_at else "",
            payment_status=order.payment_status,
        )

    @staticmethod
    async def _build_single_response(order: Order, db: AsyncSession) -> OrderResponse:
        """Build OrderResponse from an Order object (no permission check)."""
        tour_date_str = await OrderService._load_tour_date_str(db, order.tour_date_id)

        tour_name = None
        attraction_name = None
        if order.tour_id:
            trans_result = await db.execute(
                select(TourTranslation).where(
                    TourTranslation.tour_id == order.tour_id,
                ).limit(1)
            )
            translation = trans_result.scalars().first()
            if translation:
                tour_name = translation.name
        if order.attraction_id:
            attr_result = await db.execute(
                select(Attraction).where(Attraction.id == order.attraction_id)
            )
            attr = attr_result.scalar_one_or_none()
            if attr:
                for t in (attr.translations or []):
                    if t.locale == "en":
                        attraction_name = t.name
                        break

        return OrderResponse(
            id=order.id,
            order_no=order.order_no,
            tour_id=order.tour_id,
            tour_name=tour_name,
            tour_date=tour_date_str,
            attraction_id=order.attraction_id,
            attraction_name=attraction_name,
            status=order.status,
            pax_count=order.pax_count,
            total=order.total,
            currency=order.currency or "USD",
            contact_name=order.contact_name or "",
            contact_email=order.contact_email or "",
            created_at=order.created_at.isoformat() if order.created_at else "",
            payment_status=order.payment_status,
        )

    async def list_user_orders(
        self, db: AsyncSession, user: User
    ) -> OrderListResponse:
        orders = await crud_order.get_by_user(db, user_id=user.id)
        result_list = [await self._build_single_response(o, db) for o in orders]
        return OrderListResponse(orders=result_list)

    async def get_order(
        self, db: AsyncSession, order_id: UUID, user: User
    ) -> OrderResponse:
        order = await crud_order.get(db, order_id)
        if not order or order.user_id != user.id:
            raise NotFoundException(detail="Order not found")
        return await self._build_single_response(order, db)


order_service = OrderService()
