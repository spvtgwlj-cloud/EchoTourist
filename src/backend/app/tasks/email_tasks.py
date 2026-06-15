"""邮件发送 Celery 任务。"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="app.tasks.email_tasks.send_welcome_email",
    max_retries=3,
    default_retry_delay=30,
)
def send_welcome_email(user_email: str, user_name: str) -> bool:
    """异步发送欢迎邮件。"""
    import asyncio

    from app.services.email_service import render_welcome_email, send_email

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

    from app.services.email_service import render_booking_confirmation, send_email

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


@shared_task(
    name="app.tasks.email_tasks.send_review_notification",
    max_retries=3,
    default_retry_delay=30,
)
def send_review_notification(
    tour_name: str,
    tour_slug: str,
    reviewer_name: str,
    rating: int,
    title: str | None,
    comment: str | None,
    admin_email: str,
) -> bool:
    """异步发送评价通知给管理员/商家。"""
    import asyncio

    from app.services.email_service import render_review_notification, send_email

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        html = render_review_notification(tour_name, tour_slug, reviewer_name, rating, title, comment)
        result = loop.run_until_complete(
            send_email(
                admin_email,
                f"New Review: {rating}★ for {tour_name}",
                html,
            )
        )
        return result
    except Exception as e:
        logger.error(f"Failed to send review notification: {e}")
        return False
    finally:
        loop.close()


@shared_task(
    name="app.tasks.email_tasks.send_custom_tour_notification",
    max_retries=3,
    default_retry_delay=30,
)
def send_custom_tour_notification(
    user_email: str,
    contact_name: str,
    request_no: str,
    pax_count: int,
    subtotal: float,
    confirmed_price: float | None,
    currency: str,
    segments_count: int,
    total_days: int,
) -> bool:
    """异步发送定制旅程报价确认邮件给客户。"""
    import asyncio

    from app.services.email_service import render_custom_tour_notification, send_email

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        html = render_custom_tour_notification(
            request_no=request_no,
            contact_name=contact_name,
            pax_count=pax_count,
            subtotal=subtotal,
            confirmed_price=confirmed_price,
            currency=currency,
            segments_count=segments_count,
            total_days=total_days,
        )
        result = loop.run_until_complete(
            send_email(
                user_email,
                f"Your Custom Tour Quote — {request_no}",
                html,
            )
        )
        return result
    except Exception as e:
        logger.error(f"Failed to send custom tour notification: {e}")
        return False
    finally:
        loop.close()
