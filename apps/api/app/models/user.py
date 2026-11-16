"""用户主体模型。"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 学号唯一；对外不暴露业务含义（对外用自增 id）
    student_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    # student / admin（管理员不可参与交易）
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="student")
    # 是否通过实名认证
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    banned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    # 学院/专业/年级标签（用于 AI 匹配）
    college: Mapped[str | None] = mapped_column(String(64), nullable=True)
    major: Mapped[str | None] = mapped_column(String(64), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # 信用分，回流到下一轮匹配与推荐排序
    credit_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    # 头像对象键（S3）
    avatar_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
