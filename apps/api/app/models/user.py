"""用户主体模型。"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 登录账号：手机号或邮箱，唯一
    account: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    # 展示昵称（2～20 字）
    nickname: Mapped[str] = mapped_column(String(40), nullable=False)
    # 学号：实名认证后回填，可空；唯一（防冒用）
    student_no: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    # 学院/专业/年级标签（用于 AI 匹配）
    college: Mapped[str | None] = mapped_column(String(64), nullable=True)
    major: Mapped[str | None] = mapped_column(String(64), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # 实名姓名（不对外展示）
    name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # 信用分，区间 [0,100]，默认 60
    credit_score: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    # 是否通过实名认证
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # student / admin（管理员不可参与交易）
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="student")
    banned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    ban_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # 头像对象键（S3）
    avatar_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
