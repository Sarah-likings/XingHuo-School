"""任务模型（任务大厅展示主体）。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
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
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # 金额一律 DECIMAL(10,2)，Python 侧 Decimal，禁止 float
    reward: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # 地点，可填「线上」
    place: Mapped[str] = mapped_column(String(80), nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # open / assigned / cancelled（任务层面的粗状态）
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="OPEN")
    # 有效申请人数（计数冗余，由应用层维护）
    apply_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    # 是否由 AI 草稿生成
    ai_draft: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
