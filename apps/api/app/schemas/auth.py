"""认证出入参 schema（注册 / 登录 / 用户信息）。"""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 手机号：11 位，1 开头
_PHONE_RE = re.compile(r"^1\d{10}$")
# 邮箱：标准格式
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# 密码需同时包含字母与数字
_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


class RegisterRequest(BaseModel):
    account: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=32)
    nickname: str = Field(min_length=2, max_length=20)

    @field_validator("account")
    @classmethod
    def account_is_phone_or_email(cls, v: str) -> str:
        if not (_PHONE_RE.match(v) or _EMAIL_RE.match(v)):
            raise ValueError("账号需为手机号或邮箱")
        return v

    @field_validator("password")
    @classmethod
    def password_contains_letter_and_digit(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError("密码需同时包含字母和数字")
        return v


class LoginRequest(BaseModel):
    account: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=64)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account: str
    nickname: str
    student_no: str | None
    name: str | None
    role: str
    verified: bool
    college: str | None
    major: str | None
    grade: str | None
    credit_score: int
