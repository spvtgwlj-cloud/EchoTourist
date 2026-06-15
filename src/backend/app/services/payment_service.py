"""支付业务逻辑服务。"""

import logging
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.crud.order import crud_order
from app.models.tour import TourDate, TourTranslation
from app.schemas.order import PaymentIntentResponse
from app.tasks.email_tasks import send_booking_confirmation

logger = logging.getLogger(__name__)


class PaymentService:
    async def create_checkout_session(
        self, db: AsyncSession, *, order_id: str
    ) -> PaymentIntentResponse:
        try:
            order_uuid = UUID(order_id)
        except ValueError:
            raise ValidationException(detail="Invalid order_id")

        order = await crud_order.get(db, order_uuid)
        if not order:
            raise NotFoundException(detail="Order not found")

        if order.payment_status == "paid":
            raise ValidationException(detail="Order has already been paid")

        if not settings.stripe_secret_key:
            return PaymentIntentResponse(
                client_secret="mock_secret",
                session_id=f"mock_session_{order.order_no}",
            )

        stripe.api_key = settings.stripe_secret_key
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": (order.currency or "usd").lower(),
                        "product_data": {"name": f"Order {order.order_no}"},
                        "unit_amount": int(order.total * 100),
                    },
                    "quantity": 1,
                }],
                success_url=f"{settings.frontend_url}/checkout/success?order_no={order.order_no}",
                cancel_url=f"{settings.frontend_url}/checkout",
                customer_email=order.contact_email or None,
                metadata={"order_id": str(order.id)},
            )
            order.stripe_session_id = session.id
            await db.flush()
            return PaymentIntentResponse(
                client_secret=session.id,
                session_id=session.id,
            )
        except stripe.error.StripeError as e:
            raise ValidationException(detail=str(e))

    async def handle_webhook(
        self, db: AsyncSession, *, payload: bytes, signature: str | None
    ) -> dict:
        if not settings.stripe_webhook_secret or not settings.stripe_secret_key:
            return {"status": "ignored", "detail": "Stripe not configured"}

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.stripe_webhook_secret
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            raise ValidationException(detail="Invalid webhook signature")

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            order = await crud_order.get_by_stripe_session(db, session["id"])
            if order:
                order.status = "confirmed"
                order.payment_status = "paid"
                await db.flush()

                # 异步发送预订确认邮件
                await self._send_booking_email(db, order)

        return {"status": "received"}

    async def _send_booking_email(self, db: AsyncSession, order) -> None:
        """支付成功后发送预订确认邮件。"""
        if not order.contact_email:
            logger.warning(
                "No contact email for order %s, skipping booking email",
                order.order_no,
            )
            return

        # 获取产品名称（优先使用订单 locale 对应的翻译）
        trans_result = await db.execute(
            select(TourTranslation).where(
                TourTranslation.tour_id == order.tour_id,
                TourTranslation.locale == (order.locale or "en"),
            )
        )
        translation = trans_result.scalar_one_or_none()
        tour_name = translation.name if translation else f"Tour {str(order.tour_id)[:8]}"

        # 获取团期日期
        date_str = ""
        if order.tour_date_id:
            date_result = await db.execute(
                select(TourDate).where(TourDate.id == order.tour_date_id)
            )
            tour_date = date_result.scalar_one_or_none()
            if tour_date and tour_date.start_date:
                date_str = tour_date.start_date.isoformat()

        # 通过 Celery 异步发送邮件（.delay() 仅向 Redis 推送消息，不阻塞）
        send_booking_confirmation.delay(
            order_no=order.order_no,
            tour_name=tour_name,
            date=date_str,
            pax=order.pax_count,
            total=order.total,
            currency=order.currency or "USD",
            user_email=order.contact_email,
        )
        logger.info(
            "Dispatched booking confirmation email for order %s to %s",
            order.order_no,
            order.contact_email,
        )


payment_service = PaymentService()
