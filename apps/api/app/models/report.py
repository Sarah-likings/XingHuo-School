"""举报 / 申诉模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Report(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 关联订单（内容举报为空）
    order_id: Mapped[int | None] = mapped_column(ForeignKey("order.id"), nullable=True)
    # 举报对象类型：TASK / POST / USER / ORDER
    target_type: Mapped[str] = mapped_column(String(12), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    # 举报/申诉原因类型
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    # 说明（10～300 字）
    detail: Mapped[str] = mapped_column(String(600), nullable=False)
    evidence_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # pending / decided / rejected
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True)
    # 裁决结果：REFUND / SETTLE
    decision: Mapped[str | None] = mapped_column(String(12), nullable=True)
    handled_by: Mapped[int | None] = mapped_column(ForeignKey("user.id"), nullable=True)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
