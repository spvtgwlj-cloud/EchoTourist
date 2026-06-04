"""邮件发送 Celery 任务。"""

import logging

from celery import shared_task
from app.services.email_service import send_email, render_welcome_email, render_booking_confirmation

logger = logging.getLogger(__name__)


@shared_task(
    name="app.tasks.email_tasks.send_welcome_email",
    max_retries=3,
    default_retry_delay=30,
)
def send_welcome_email(user_email: str, user_name: str) -> bool:
    """异步发送欢迎邮件。"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        html = render_welcome_email(user_name)
        result = loop.run_until_complete(send_email(user_email, "Welcome to Echo Tours!", html))
        return result
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return False
    finally:
        loop.close()


@shared_task(
    name="app.tasks.email_tasks.send_booking_confirmation",
    max_retries=3,
    default_retry_delay=30,
)
def send_booking_confirmation(order_no: str, tour_name: str, date: str, pax: int, total: float, currency: str, user_email: str) -> bool:
    """异步发送预订确认邮件。"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        html = render_booking_confirmation(order_no, tour_name, date, pax, total, currency)
        result = loop.run_until_complete(
            send_email(user_email, f"Booking Confirmed — {order_no}", html)
        )
        return result
    except Exception as e:
        logger.error(f"Failed to send booking confirmation: {e}")
        return False
    finally:
        loop.close()
