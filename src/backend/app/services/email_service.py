"""SendGrid 邮件发送服务。"""

# ruff: noqa: E501 — allow long lines in HTML templates (inline CSS in f-strings)

import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
) -> bool:
    """发送邮件。如果 SendGrid 未配置，仅记录日志。"""
    if not settings.sendgrid_api_key:
        logger.info(f"[EMAIL MOCK] To: {to_email} | Subject: {subject}")
        return True

    try:
        import sendgrid
        from sendgrid.helpers.mail import Content, Email, Mail, To

        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        mail = Mail(
            from_email=Email("noreply@echotours.com"),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content),
        )
        response = sg.client.mail.send.post(request_body=mail.get())
        logger.info(f"Email sent to {to_email}: {response.status_code}")
        return 200 <= response.status_code < 300
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def render_welcome_email(name: str) -> str:
    return f"""
    <html>
    <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h1>Welcome to Echo Tours, {name}!</h1>
        <p>Thank you for creating an account. Start exploring amazing tours worldwide.</p>
        <p><a href="{settings.frontend_url}/tours" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Browse Tours</a></p>
        <hr>
        <p style="color: #666; font-size: 12px;">Echo Tours — Your Journey, Our Passion</p>
    </body>
    </html>
    """


def render_booking_confirmation(order_no: str, tour_name: str, date: str, pax: int, total: float, currency: str) -> str:
    return f"""
    <html>
    <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h1>Booking Confirmed!</h1>
        <p>Your tour has been booked successfully.</p>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Order</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{order_no}</strong></td></tr>            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Tour</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{tour_name}</strong></td></tr>            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Date</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{date}</strong></td></tr>            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Guests</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{pax}</strong></td></tr>            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Total</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{total:.2f} {currency}</strong></td></tr>        </table>
        <p><a href="{settings.frontend_url}/user/orders" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">View Order</a></p>        <hr>
        <p style="color: #666; font-size: 12px;">Echo Tours — Your Journey, Our Passion</p>
    </body>
    </html>
    """


def render_review_notification(
    tour_name: str,
    tour_slug: str,
    reviewer_name: str,
    rating: int,
    title: str | None,
    comment: str | None,
) -> str:
    """生成评价通知的 HTML 邮件内容（管理员/商家收到新评价时）。"""
    stars = "⭐" * rating + "☆" * (5 - rating)
    title_html = f"<p><strong>Subject:</strong> {title}</p>" if title else ""
    comment_html = f"<blockquote style=\"border-left: 4px solid #ddd; margin: 12px 0; padding: 8px 16px; color: #555;\">{comment}</blockquote>" if comment else ""

    return f"""
    <html>
    <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h1>New Review Alert</h1>
        <p>A customer has left a new review for your tour.</p>
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Tour</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{tour_name}</strong></td></tr>            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Reviewer</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{reviewer_name}</strong></td></tr>            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Rating</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong style="font-size: 18px;">{stars} {rating}/5</strong></td></tr>        </table>
        {title_html}
        {comment_html}
        <p><a href="{settings.frontend_url}/tours/{tour_slug}" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">View Tour</a></p>        <hr>
        <p style="color: #666; font-size: 12px;">Echo Tours — Review Notification</p>
    </body>
    </html>
    """


def render_custom_tour_notification(
    request_no: str,
    contact_name: str,
    pax_count: int,
    subtotal: float,
    confirmed_price: float | None,
    currency: str,
    segments_count: int,
    total_days: int,
) -> str:
    """生成定制旅程报价通知的 HTML 邮件内容（管理员确认价格后发送给客户）。"""
    price_html = ""
    if confirmed_price is not None:
        currency_symbol = "$" if currency == "USD" else currency
        price_html = f"""
        <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Request</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{request_no}</strong></td></tr>            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Estimated Price</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{currency_symbol}{subtotal:.2f}</strong></td></tr>            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Confirmed Price</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong style="font-size: 18px; color: #16a34a;">{currency_symbol}{confirmed_price:.2f}</strong></td></tr>            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Travelers</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{pax_count}</strong></td></tr>            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Itinerary</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{segments_count} segment(s), {total_days} days</strong></td></tr>        </table>"""

    return f"""
    <html>
    <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h1>Your Custom Tour Quote is Ready!</h1>
        <p>Dear {contact_name},</p>
        <p>Great news! Our team has reviewed your custom tour request and the price has been confirmed.</p>
        {price_html}
        <p>You can view the full details of your custom itinerary by logging into your account.</p>
        <p><a href="{settings.frontend_url}/user/custom-requests" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">View My Requests</a></p>        <p style="color: #666; font-size: 13px;">If you have any questions, please don't hesitate to contact us.</p>
        <hr>
        <p style="color: #666; font-size: 12px;">Echo Tours — Your Journey, Our Passion</p>
    </body>
    </html>
    """
