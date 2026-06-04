"""核心基础设施测试 —— 异常层次、错误处理器、响应格式。"""

import pytest
from app.core.exceptions import (
    AppException,
    NotFoundException,
    ValidationException,
    AuthenticationException,
    PermissionDeniedException,
    ConflictException,
    InsufficientStockException,
    ServiceUnavailableException,
)
from app.core.response import success_response, paginated_response, error_response


# ============================================================
# 功能测试：异常层次
# ============================================================

def test_app_exception_defaults():
    """AppException 应该有合理的默认值。"""
    exc = AppException()
    assert exc.detail == "An error occurred"
    assert exc.status_code == 500
    assert exc.error_code is None


def test_app_exception_custom():
    """AppException 应该接受自定义参数。"""
    exc = AppException(detail="Custom error", status_code=418, error_code="TEAPOT")
    assert exc.detail == "Custom error"
    assert exc.status_code == 418
    assert exc.error_code == "TEAPOT"


class TestSpecificExceptions:
    """测试各个特定异常的正确状态码和默认消息。"""

    def test_not_found(self):
        exc = NotFoundException()
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"
        assert exc.detail == "Resource not found"

    def test_not_found_custom(self):
        exc = NotFoundException(detail="Tour not found")
        assert exc.detail == "Tour not found"

    def test_validation(self):
        exc = ValidationException()
        assert exc.status_code == 422
        assert exc.error_code == "VALIDATION_ERROR"

    def test_authentication(self):
        exc = AuthenticationException()
        assert exc.status_code == 401
        assert exc.error_code == "UNAUTHORIZED"

    def test_permission_denied(self):
        exc = PermissionDeniedException()
        assert exc.status_code == 403
        assert exc.error_code == "FORBIDDEN"

    def test_conflict(self):
        exc = ConflictException()
        assert exc.status_code == 409
        assert exc.error_code == "CONFLICT"

    def test_insufficient_stock(self):
        exc = InsufficientStockException()
        assert exc.status_code == 400
        assert exc.error_code == "INSUFFICIENT_STOCK"

    def test_service_unavailable(self):
        exc = ServiceUnavailableException()
        assert exc.status_code == 503
        assert exc.error_code == "SERVICE_UNAVAILABLE"


# ============================================================
# 功能测试：异常继承关系
# ============================================================

class TestExceptionInheritance:
    """验证所有业务异常都继承自 AppException。"""

    def test_not_found_is_app_exception(self):
        assert isinstance(NotFoundException(), AppException)

    def test_validation_is_app_exception(self):
        assert isinstance(ValidationException(), AppException)

    def test_authentication_is_app_exception(self):
        assert isinstance(AuthenticationException(), AppException)

    def test_all_are_exceptions(self):
        """所有异常都能被标准的 except Exception 捕获。"""
        for exc_cls in [
            NotFoundException, ValidationException, AuthenticationException,
            PermissionDeniedException, ConflictException, InsufficientStockException,
            ServiceUnavailableException,
        ]:
            assert isinstance(exc_cls(), Exception)


# ============================================================
# 功能测试：统一响应格式
# ============================================================

class TestResponseFormat:
    """测试统一响应格式的正确性。"""

    def test_success_response(self):
        resp = success_response(data={"id": "123"}, message="ok")
        assert resp["code"] == 200
        assert resp["data"] == {"id": "123"}
        assert resp["message"] == "ok"

    def test_success_response_default_message(self):
        resp = success_response(data=[])
        assert resp["message"] == "ok"

    def test_success_response_none_data(self):
        resp = success_response(data=None)
        assert resp["data"] is None

    def test_paginated_response(self):
        resp = paginated_response(
            data=[{"id": "1"}, {"id": "2"}],
            total=10,
            page=1,
            page_size=12,
        )
        assert resp["code"] == 200
        assert len(resp["data"]) == 2
        assert resp["meta"]["total"] == 10
        assert resp["meta"]["page"] == 1
        assert resp["meta"]["page_size"] == 12

    def test_paginated_response_empty(self):
        """边界测试：空列表的分页响应。"""
        resp = paginated_response(data=[], total=0, page=1, page_size=12)
        assert resp["meta"]["total"] == 0
        assert resp["data"] == []

    def test_paginated_response_last_page(self):
        """边界测试：最后一页（数据不足 page_size）。"""
        resp = paginated_response(data=[{"id": "1"}], total=13, page=2, page_size=12)
        assert len(resp["data"]) == 1

    def test_error_response(self):
        resp = error_response(detail="Something went wrong", error_code="ERROR", status_code=400)
        assert resp["code"] == 400
        assert resp["data"] is None
        assert resp["message"] == "Something went wrong"

    def test_error_response_defaults(self):
        resp = error_response(detail="Not found")
        assert resp["code"] == 400
        assert resp["error_code"] == "ERROR"


# ============================================================
# 边界测试：异常构造极端输入
# ============================================================

class TestExceptionEdgeCases:
    """异常类的边界输入测试。"""

    def test_empty_detail(self):
        exc = AppException(detail="")
        assert exc.detail == ""

    def test_zero_status_code(self):
        exc = AppException(detail="test", status_code=0)
        assert exc.status_code == 0

    def test_none_error_code(self):
        exc = AppException(detail="test", error_code=None)
        assert exc.error_code is None

    def test_unicode_detail(self):
        exc = NotFoundException(detail="资源未找到 🏔️")
        assert "资源未找到" in exc.detail
