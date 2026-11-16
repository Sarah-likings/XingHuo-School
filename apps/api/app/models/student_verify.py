"""学生证实名认证模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class StudentVerify(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "student_verify"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 一个用户只有一条认证记录
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, nullable=False)
    # pending / approved / rejected
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True)
    student_no: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    college: Mapped[str | None] = mapped_column(String(64), nullable=True)
    major: Mapped[str | None] = mapped_column(String(64), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # 学生证影像对象键（S3，敏感信息：加密存储、签名访问、查看留痕）
    image_key: Mapped[str] = mapped_column(String(255), nullable=False)
    reject_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
