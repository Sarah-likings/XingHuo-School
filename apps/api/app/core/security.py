"""鉴权与脱敏工具：JWT 签发/校验、bcrypt 密码哈希、敏感信息脱敏。"""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

# ---- 密码哈希 ----


def hash_password(password: str) -> str:
    """bcrypt 哈希，返回字符串存库。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# ---- JWT ----


def create_access_token(user_id: int, role: str, verified: bool) -> str:
    """签发 access token，claims 含 sub/role/verified/exp（见《技术要求》4.3）。"""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "verified": verified,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    """校验并解析 token，失败抛 jwt 异常由调用方转 401。"""
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


# ---- 脱敏（日志与异常信息里不得出现明文）----


def mask_student_no(student_no: str) -> str:
    """学号脱敏：保留前 3 后 2 位。"""
    if len(student_no) <= 5:
        return "*" * len(student_no)
    return f"{student_no[:3]}{'*' * (len(student_no) - 5)}{student_no[-2:]}"


def mask_phone(phone: str) -> str:
    """手机号脱敏：保留前 3 后 4 位。"""
    if len(phone) != 11:
        return "***"
    return f"{phone[:3]}****{phone[-4:]}"
