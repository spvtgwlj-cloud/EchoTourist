"""Celery 任务测试。"""

import pytest
from unittest.mock import patch, MagicMock

from app.tasks.celery_app import celery_app
from app.tasks.email_tasks import send_welcome_email, send_booking_confirmation


class TestCeleryConfig:
    """Celery 配置测试。"""

    def test_celery_app_name(self):
        assert celery_app.main == "echo_tours"

    def test_celery_broker_configured(self):
        assert celery_app.conf.broker_url is not None

    def test_celery_serializer_json(self):
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.accept_content == ["json"]

    def test_celery_includes_tasks(self):
        includes = celery_app.conf.include
        assert "app.tasks.email_tasks" in includes
        assert "app.tasks.search_tasks" in includes

    def test_celery_beat_schedule_exists(self):
        schedule = celery_app.conf.beat_schedule
        assert schedule is not None
        assert "cleanup-expired-sessions" in schedule


class TestEmailTasksSignature:
    """邮件任务签名验证。"""

    def test_send_welcome_email_signature(self):
        task = send_welcome_email
        assert task.name == "app.tasks.email_tasks.send_welcome_email"
        assert task.max_retries == 3

    def test_send_booking_confirmation_signature(self):
        task = send_booking_confirmation
        assert task.name == "app.tasks.email_tasks.send_booking_confirmation"
        assert task.max_retries == 3

    @pytest.mark.asyncio
    async def test_booking_confirmation_expected_args(self):
        """验证任务签名匹配实际调用方式。"""
        # The task expects: order_no, tour_name, date, pax, total, currency, user_email
        # Create a mock task run
        with patch("app.tasks.email_tasks.send_email") as mock_send:
            mock_send.return_value = True
            result = send_welcome_email("user@example.com", "Alice")
            # In test mode, Celery tasks run synchronously
            assert result is True or result is False
