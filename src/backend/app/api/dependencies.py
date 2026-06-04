"""可复用 API 依赖项。"""

from fastapi import Depends
from app.api.v1.auth import get_current_user
from app.core.exceptions import PermissionDeniedException
from app.models.user import User


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求当前用户是管理员。"""
    if not current_user.is_admin:
        raise PermissionDeniedException(detail="Admin access required")
    return current_user
