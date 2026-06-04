"""SendGrid 邮件发送服务。"""

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
        from sendgrid.helpers.mail import Mail, Email, To, Content

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
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Order</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{order_no}</strong></td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Tour</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{tour_name}</strong></td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Date</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{date}</strong></td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Guests</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{pax}</strong></td></tr>
            <tr><td style="padding: 8px; border-bottom: 1px solid #eee;">Total</td><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>{total:.2f} {currency}</strong></td></tr>
        </table>
        <p><a href="{settings.frontend_url}/user/orders" style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">View Order</a></p>
        <hr>
        <p style="color: #666; font-size: 12px;">Echo Tours — Your Journey, Our Passion</p>
    </body>
    </html>
    """
