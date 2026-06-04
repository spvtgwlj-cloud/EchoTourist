"""统一错误处理中间件，将 AppException 转换为标准 JSON 响应。"""

from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import AppException


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """捕获未预期的异常，返回 500。"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
        },
    )


def register_error_handlers(app):
    """在 FastAPI app 上注册所有异常处理器。"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
