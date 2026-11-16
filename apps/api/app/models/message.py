"""私聊消息模型。"""

from sqlalchemy import ForeignKey, Integer, String, Text
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
    # text / image
    type: Mapped[str] = mapped_column(String(16), nullable=False, default="text")
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
