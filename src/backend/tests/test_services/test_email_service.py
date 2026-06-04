"""邮件服务测试。"""

from app.services.email_service import (
    send_email,
    render_welcome_email,
    render_booking_confirmation,
)


class TestEmailRendering:
    """邮件模板渲染测试。"""

    def test_welcome_email_contains_name(self):
        html = render_welcome_email("Alice")
        assert "Alice" in html
        assert "Welcome" in html
        assert "Browse Tours" in html

    def test_welcome_email_has_link(self):
        html = render_welcome_email("Bob")
        assert "href=" in html
        assert "http" in html

    def test_booking_confirmation_contains_details(self):
        html = render_booking_confirmation(
            order_no="ECHO-20260601-ABC123",
            tour_name="Great Wall Hiking",
            date="2026-07-15",
            pax=2,
            total=2400.00,
            currency="USD",
        )
        assert "ECHO-20260601-ABC123" in html
        assert "Great Wall Hiking" in html
        assert "2,400.00" in html or "2400.00" in html
        assert "USD" in html

    def test_booking_confirmation_has_cta(self):
        html = render_booking_confirmation(
            order_no="ECHO-001", tour_name="Test", date="2026-01-01",
            pax=1, total=100, currency="USD",
        )
        assert "View Order" in html

    def test_welcome_email_empty_name(self):
        """边界测试：空名称。"""
        html = render_welcome_email("")
        assert "Welcome to Echo Tours" in html


class TestEmailSend:
    """邮件发送功能测试（mock 模式）。"""

    async def test_send_email_mock_mode(self):
        """未配置 SendGrid 时以 mock 模式发送（返回 True）。"""
        result = await send_email(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>",
        )
        assert result is True

    async def test_send_email_empty_subject(self):
        """边界测试：空主题。"""
        result = await send_email(
            to_email="test@example.com",
            subject="",
            html_content="<p>content</p>",
        )
        assert result is True

    async def test_send_email_empty_content(self):
        """边界测试：空内容。"""
        result = await send_email(
            to_email="test@example.com",
            subject="Test",
            html_content="",
        )
        assert result is True
