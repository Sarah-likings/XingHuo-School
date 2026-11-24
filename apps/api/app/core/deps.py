"""FastAPI 依赖注入：鉴权与权限校验。"""

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotVerifiedError, UnauthorizedError
from app.core.security import decode_token
from app.models.user import User


def get_current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    """解析 JWT（httpOnly Cookie），返回 User ORM 对象。未登录/无效抛 401。"""
    token = request.cookies.get("access_token")
    if not token:
        raise UnauthorizedError("未登录")
    try:
        payload = decode_token(token)
    except Exception as exc:  # noqa: BLE001 —— jwt 异常统一转 401，不暴露细节
        raise UnauthorizedError("令牌无效或已过期") from exc
    user = db.get(User, int(payload.get("sub", 0)))
    if user is None or user.deleted_at is not None:
        raise UnauthorizedError("用户不存在")
    # 记录 user_id 供日志中间件审计使用
    request.state.user_id = user.id
    return user


def require_verified(user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求已实名认证（发布/接单等写操作）。"""
    if not user.verified:
        raise NotVerifiedError()
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    """要求管理员角色（审核/仲裁/下架等）。"""
    if user.role != "admin":
        raise ForbiddenError("仅管理员可操作")
    return user
