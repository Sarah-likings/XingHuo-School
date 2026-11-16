"""认证业务：注册与登录。"""

import re

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    DuplicateError,
    TooManyRequestsError,
    UnauthorizedError,
    ValidationFailedError,
)
from app.core.redis import get_redis
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.models.wallet import Wallet
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, student_no: str, name: str, password: str) -> User:
        """注册：学号段初筛 + 查重 + 建用户与钱包（一生一账户）。"""
        if not re.fullmatch(settings.student_no_pattern, student_no):
            raise ValidationFailedError("学号格式不正确")
        if self.user_repo.find_one(student_no=student_no):
            raise DuplicateError("该学号已注册")
        user = User(
            student_no=student_no,
            name=name,
            password_hash=hash_password(password),
            role="student",
            verified=False,
            credit_score=100,
        )
        self.db.add(user)
        self.db.flush()
        self.db.add(Wallet(user_id=user.id))
        return user

    def login(self, student_no: str, password: str) -> User:
        """登录：失败锁定（Redis 计数），成功签发由 router 完成。"""
        redis = get_redis()
        lock_key = f"login_fail:{student_no}"
        if int(redis.get(lock_key) or 0) >= settings.login_max_attempts:
            raise TooManyRequestsError("登录失败次数过多，请稍后再试")

        user = self.user_repo.find_one(student_no=student_no)
        if (
            user is None
            or user.deleted_at is not None
            or not verify_password(password, user.password_hash)
        ):
            # 失败计数：首次写入设置过期，达到阈值锁定（不泄露用户是否存在）
            count = redis.incr(lock_key)
            if count == 1:
                redis.expire(lock_key, settings.login_lock_seconds)
            raise UnauthorizedError("学号或密码错误")

        redis.delete(lock_key)
        return user
