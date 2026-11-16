"""认证出入参 schema（注册 / 登录 / 用户信息）。"""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 密码需同时包含字母与数字（长度由 Field 约束）
_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


class RegisterRequest(BaseModel):
    student_no: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def password_contains_letter_and_digit(cls, v: str) -> str:
        if not _PASSWORD_RE.match(v):
            raise ValueError("密码需同时包含字母和数字")
        return v


class LoginRequest(BaseModel):
    student_no: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=64)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_no: str
    name: str
    role: str
    verified: bool
    college: str | None
    major: str | None
    grade: str | None
    credit_score: int
