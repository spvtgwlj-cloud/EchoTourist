"""自定义异常类层次，用于统一错误处理。"""

from typing import Optional


class AppException(Exception):
    """应用基础异常，所有业务异常继承此类。"""

    def __init__(
        self,
        detail: str = "An error occurred",
        status_code: int = 500,
        error_code: Optional[str] = None,
    ):
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found", error_code: str = "NOT_FOUND"):
        super().__init__(detail=detail, status_code=404, error_code=error_code)


class ValidationException(AppException):
    def __init__(self, detail: str = "Validation error", error_code: str = "VALIDATION_ERROR"):
        super().__init__(detail=detail, status_code=422, error_code=error_code)


class AuthenticationException(AppException):
    def __init__(self, detail: str = "Authentication required", error_code: str = "UNAUTHORIZED"):
        super().__init__(detail=detail, status_code=401, error_code=error_code)


class PermissionDeniedException(AppException):
    def __init__(self, detail: str = "Permission denied", error_code: str = "FORBIDDEN"):
        super().__init__(detail=detail, status_code=403, error_code=error_code)


class ConflictException(AppException):
    def __init__(self, detail: str = "Resource already exists", error_code: str = "CONFLICT"):
        super().__init__(detail=detail, status_code=409, error_code=error_code)


class InsufficientStockException(AppException):
    def __init__(self, detail: str = "Insufficient availability", error_code: str = "INSUFFICIENT_STOCK"):
        super().__init__(detail=detail, status_code=400, error_code=error_code)


class ServiceUnavailableException(AppException):
    def __init__(self, detail: str = "Service temporarily unavailable", error_code: str = "SERVICE_UNAVAILABLE"):
        super().__init__(detail=detail, status_code=503, error_code=error_code)
