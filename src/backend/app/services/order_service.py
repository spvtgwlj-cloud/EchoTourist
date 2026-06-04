"""订单业务逻辑服务。"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.order import crud_order
from app.crud.tour import crud_tour, crud_tour_date
from app.core.exceptions import NotFoundException, InsufficientStockException
from app.models.order import Order, OrderPassenger
from app.models.tour import TourDate, TourTranslation
from app.models.user import User
from app.schemas.order import BookingRequest, OrderResponse, OrderListResponse


class OrderService:
    @staticmethod
    def _generate_order_no() -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d")
        suffix = str(uuid4())[:8].upper()
        return f"ECHO-{ts}-{suffix}"

    @staticmethod
    async def _build_response(order: Order, db: AsyncSession) -> OrderResponse:
        tour_date_str = ""
        if order.tour_date_id:
            td_result = await db.execute(
                __import__("sqlalchemy").select(TourDate).where(
                    TourDate.id == order.tour_date_id
                )
            )
            td = td_result.scalar_one_or_none()
            if td and td.start_date:
                tour_date_str = td.start_date.isoformat()

        return OrderResponse(
            id=order.id,
            order_no=order.order_no,
            tour_id=order.tour_id,
            tour_name=None,
            tour_date=tour_date_str,
            status=order.status,
            pax_count=order.pax_count,
            total=order.total,
            currency=order.currency or "USD",
            contact_name=order.contact_name or "",
            contact_email=order.contact_email or "",
            created_at=order.created_at.isoformat() if order.created_at else "",
            payment_status=order.payment_status,
        )

    async def create_booking(
        self,
        db: AsyncSession,
        *,
        req: BookingRequest,
        user: User,
    ) -> OrderResponse:
        # Validate tour exists
        tour = await crud_tour.get(db, req.tour_id)
        if not tour:
            raise NotFoundException(detail="Tour not found")

        # Validate & atomically decrement availability
        tour_date = await crud_tour_date.decrement_availability(
            db, req.tour_date_id, req.pax_count
        )
        if not tour_date:
            # Check if the date exists at all or just insufficient stock
            td = await crud_tour_date.get(db, req.tour_date_id)
            if not td:
                raise NotFoundException(detail="Tour date not found")
            raise InsufficientStockException(
                detail=f"Only {td.availability} spots available"
            )

        # Get translation for tour_name
        from sqlalchemy import select as sa_select
        trans_result = await db.execute(
            sa_select(TourTranslation).where(
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

        # Invalidate tour dates cache so fresh data is returned
        try:
            from app.cache.client import get_redis
            redis = await get_redis()
            pattern = f"cache:TourService.get_tour_dates:*"
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await redis.delete(*keys)
        except Exception:
            pass

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

    async def list_user_orders(
        self, db: AsyncSession, user: User
    ) -> OrderListResponse:
        orders = await crud_order.get_by_user(db, user_id=user.id)
        result_list = [await self._build_response(o, db) for o in orders]
        return OrderListResponse(orders=result_list)

    async def get_order(
        self, db: AsyncSession, order_id: UUID, user: User
    ) -> OrderResponse:
        order = await crud_order.get(db, order_id)
        if not order or order.user_id != user.id:
            raise NotFoundException(detail="Order not found")
        return await self._build_response(order, db)


order_service = OrderService()
