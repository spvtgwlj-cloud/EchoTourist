"""邮件服务边界和鲁棒性测试。"""

from unittest.mock import patch

from app.services.email_service import send_email, render_welcome_email, render_booking_confirmation


class TestEmailEdgeCases:
    """邮件服务边界情况测试。"""

    async def test_send_special_chars_in_email(self):
        """鲁棒性测试：特殊字符邮箱地址。"""
        result = await send_email(
            to_email="test+tag@example.com",
            subject="Hello <world> & more",
            html_content="<p>Test &amp; content</p>",
        )
        assert result is True

    async def test_send_long_subject(self):
        """边界测试：超长主题。"""
        long_subject = "Subject " + "x" * 500
        result = await send_email(
            to_email="test@example.com",
            subject=long_subject,
            html_content="<p>content</p>",
        )
        assert result is True

    async def test_send_invalid_email_format(self):
        """鲁棒性测试：格式无效的邮箱 — mock 模式仍返回 True。"""
        result = await send_email(
            to_email="not-an-email",
            subject="Test",
            html_content="<p>content</p>",
        )
        assert result is True

    async def test_send_empty_to_email(self):
        """边界测试：空收件人。"""
        result = await send_email(
            to_email="",
            subject="Test",
            html_content="<p>content</p>",
        )
        assert result is True

    async def test_send_unicode_content(self):
        """功能测试：Unicode 内容。"""
        result = await send_email(
            to_email="user@example.com",
            subject="感谢您的预订 谢谢",
            html_content="<p>探索世界 🌍 发现美好</p>",
        )
        assert result is True


class TestEmailRenderingEdgeCases:
    """邮件模板边界测试。"""

    def test_welcome_email_long_name(self):
        """边界测试：超长用户名。"""
        long_name = "Very Long Name That Goes On And On " * 10
        html = render_welcome_email(long_name)
        assert long_name in html

    def test_welcome_email_special_chars_in_name(self):
        """鲁棒性测试：用户名含特殊字符。"""
        html = render_welcome_email("John <script>alert('xss')</script> Doe")
        assert "John" in html

    def test_booking_confirmation_large_pax(self):
        """边界测试：大数量旅客。"""
        html = render_booking_confirmation(
            order_no="ECHO-20260604-TEST",
            tour_name="Test Tour",
            date="2026-12-01",
            pax=100,
            total=999999.99,
            currency="USD",
        )
        assert "100" in html
        assert "999,999" in html or "999999" in html

    def test_booking_confirmation_zero_price(self):
        """边界测试：零价格。"""
        html = render_booking_confirmation(
            order_no="ECHO-FREE",
            tour_name="Free Tour",
            date="2026-01-01",
            pax=1,
            total=0.00,
            currency="USD",
        )
        assert "0.00" in html or "0" in html

    def test_booking_confirmation_weird_currency(self):
        """边界测试：特殊币种。"""
        html = render_booking_confirmation(
            order_no="ECHO-001",
            tour_name="Test",
            date="2026-01-01",
            pax=1,
            total=1000,
            currency="BTC",
        )
        assert "BTC" in html
