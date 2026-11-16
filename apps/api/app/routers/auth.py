"""认证路由：注册、登录。"""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.response import success
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, RegisterRequest, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201, summary="注册")
def register(data: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    user = AuthService(db).register(data.student_no, data.name, data.password)
    return success(data=UserOut.model_validate(user).model_dump())


@router.post("/login", summary="登录（签发 JWT httpOnly Cookie）")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)) -> dict:
    user = AuthService(db).login(data.student_no, data.password)
    token = create_access_token(user.id, user.role, user.verified)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
    )
    return success(data=UserOut.model_validate(user).model_dump())
