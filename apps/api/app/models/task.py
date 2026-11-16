"""任务模型（任务大厅展示主体）。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Task(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "task"
    __table_args__ = (
        # 高频查询：按分类 + 状态 + 截止时间筛选大厅列表
        Index("ix_task_category_status_deadline", "category", "status", "deadline"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    publisher_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    # 金额一律 DECIMAL(10,2)，Python 侧 Decimal，禁止 float
    reward: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # open / closed（任务开放状态，区别于订单状态机）
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="OPEN")
