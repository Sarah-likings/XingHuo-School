"""生活帖模型。"""

from sqlalchemy import ARRAY, JSON, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Post(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "post"
    __table_args__ = (Index("ix_post_audit_created", "audit_status", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 图片对象键数组（≤9）；SQLite 下退化为 TEXT
    images: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(256)).with_variant(JSON, "sqlite"), nullable=True
    )
    # pending / approved / rejected（内容审核状态）
    audit_status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    reject_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
