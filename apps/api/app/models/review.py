"""双向评价模型。"""

from sqlalchemy import Boolean, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Review(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "review"
    __table_args__ = (
        # 同一订单同一评价人只能评一次
        UniqueConstraint("order_id", "from_user", name="uq_review_order_from"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id"), nullable=False)
    from_user: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    to_user: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 是否超期评价
    is_late: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
