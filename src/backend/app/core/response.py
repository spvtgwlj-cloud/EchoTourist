"""API 统一响应格式。"""

from typing import Any


def success_response(data: Any, message: str = "ok") -> dict:
    return {"code": 200, "data": data, "message": message}


def paginated_response(
    data: Any,
    total: int,
    page: int = 1,
    page_size: int = 12,
    message: str = "ok",
) -> dict:
    return {
        "code": 200,
        "data": data,
        "message": message,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


def error_response(detail: str, error_code: str = "ERROR", status_code: int = 400) -> dict:
    return {
        "code": status_code,
        "data": None,
        "message": detail,
        "error_code": error_code,
    }
