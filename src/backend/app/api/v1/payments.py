from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import PaymentIntentResponse
from app.services.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Checkout Session for an existing order."""
    order_id = body.get("order_id", "")
    return await payment_service.create_checkout_session(db, order_id=order_id)


@router.post("/stripe-webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    return await payment_service.handle_webhook(
        db, payload=payload, signature=sig_header
    )
