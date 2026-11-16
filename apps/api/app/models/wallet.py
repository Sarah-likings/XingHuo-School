"""钱包模型（双账：可用 / 冻结）。"""

from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class Wallet(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "wallet"
    __table_args__ = (
        # 可用余额非负：CHECK + 条件更新双重保证
        CheckConstraint("available >= 0", name="ck_wallet_available_nonneg"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), unique=True, nullable=False)
    available: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    frozen: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
