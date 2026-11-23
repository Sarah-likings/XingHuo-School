"""私聊会话模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class ChatSession(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "chat_session"
    __table_args__ = (
        # 同一任务同一接单人只有一条会话
        UniqueConstraint("task_id", "taker_id", name="uq_chat_session_task_taker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("task.id"), nullable=False)
    # 会话双方（employer 为雇主，taker 为申请者）
    employer_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    taker_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    last_msg_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unread_employer: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unread_taker: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
