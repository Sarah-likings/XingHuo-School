"""举报 / 申诉模型。"""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Report(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("order.id"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    # pending / resolved
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True)
