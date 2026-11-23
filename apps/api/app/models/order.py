"""订单模型（履约与状态机主体，同时承载「申请记录」）。

选定前每行是一条申请（status=OPEN，同一 task 可多条）；选定后该行成为成交订单。
"""

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
    text,
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
        # 部分唯一：成交订单（status != OPEN）的 task_id 唯一，防双主；申请行（OPEN）可多条
        Index(
            "uq_order_task_traded",
            "task_id",
            unique=True,
            postgresql_where=text("status != 'OPEN'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"), nullable=False)
    employer_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    taker_id: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=OrderStatus.OPEN.value)
    # 冻结金额快照：选定前为 NULL，选定后写入
    reward: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    # 申请留言
    apply_note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # 选定操作的幂等键
    idem_key: Mapped[str | None] = mapped_column(String(40), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
