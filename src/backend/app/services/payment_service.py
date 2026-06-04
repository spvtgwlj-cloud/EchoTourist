"""支付业务逻辑服务。"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.crud.order import crud_order
from app.schemas.order import PaymentIntentResponse

import stripe


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

        return {"status": "received"}


payment_service = PaymentService()
