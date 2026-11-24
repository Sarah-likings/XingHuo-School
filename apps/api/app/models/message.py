"""私聊消息模型。"""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Message(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_session.id"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    # TEXT / IMAGE
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="TEXT")
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # 对方是否已读
    read_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
