"""订单模型（履约与状态机主体）。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import OrderStatus
from app.models.base import SoftDeleteMixin, TimestampMixin

_ORDER_STATUSES = [s.value for s in OrderStatus]


class Order(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "order"
    __table_args__ = (
        # 状态枚举用 VARCHAR + CHECK（不用 PG enum，便于扩展）
        CheckConstraint(
            f"status IN ({', '.join(repr(s) for s in _ORDER_STATUSES)})",
            name="ck_order_status",
        ),
        # 高频查询：接单人按状态筛单
        Index("ix_order_taker_status", "taker_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 一个任务只有一个订单（UNIQUE 兜底，防双主）
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"), unique=True, nullable=False)
    employer_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    taker_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=OrderStatus.OPEN.value)
    # 悬赏金额快照
    reward: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
