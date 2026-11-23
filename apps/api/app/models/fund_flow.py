"""资金流水模型（只增不改不删，用于每日对账）。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FundFlow(Base):
    __tablename__ = "fund_flow"
    __table_args__ = (Index("ix_fund_flow_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("order.id"), nullable=True)
    # recharge / freeze / settle / refund / clear
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # 必须写 balance_after 便于核对
    balance_after: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    remark: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
