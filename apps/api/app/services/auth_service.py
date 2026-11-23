"""认证业务：注册与登录。"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    DuplicateError,
    TooManyRequestsError,
    UnauthorizedError,
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

    def register(self, account: str, password: str, nickname: str) -> User:
        """注册：账号（手机/邮箱）唯一校验 + 建用户与钱包。学号留待实名认证回填。"""
        if self.user_repo.find_one(account=account):
            raise DuplicateError("该账号已注册")
        user = User(
            account=account,
            password_hash=hash_password(password),
            nickname=nickname,
            role="student",
            verified=False,
            credit_score=60,
        )
        self.db.add(user)
        self.db.flush()
        self.db.add(Wallet(user_id=user.id))
        return user

    def login(self, account: str, password: str) -> User:
        """登录：失败锁定（Redis 计数），成功签发由 router 完成。"""
        redis = get_redis()
        lock_key = f"login_fail:{account}"
        if int(redis.get(lock_key) or 0) >= settings.login_max_attempts:
            raise TooManyRequestsError("登录失败次数过多，请稍后再试")

        user = self.user_repo.find_one(account=account)
        if (
            user is None
            or user.deleted_at is not None
            or not verify_password(password, user.password_hash)
        ):
            # 失败计数：首次写入设置过期，达到阈值锁定（不泄露账号是否存在）
            count = redis.incr(lock_key)
            if count == 1:
                redis.expire(lock_key, settings.login_lock_seconds)
            raise UnauthorizedError("账号或密码错误")

        redis.delete(lock_key)
        return user
