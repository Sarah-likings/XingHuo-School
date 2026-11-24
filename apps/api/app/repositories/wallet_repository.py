"""钱包数据访问（条件更新，以影响行数/返回值判定胜负）。"""

from decimal import Decimal

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.wallet import Wallet
from app.repositories.base import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Wallet)

    def freeze(self, user_id: int, amount: Decimal) -> Decimal | None:
        """冻结：available -= amount, frozen += amount（available >= amount 才成功）。

        返回更新后的 available（即 balance_after），余额不足返回 None。
        """
        stmt = (
            update(Wallet)
            .where(Wallet.user_id == user_id, Wallet.available >= amount)
            .values(
                available=Wallet.available - amount,
                frozen=Wallet.frozen + amount,
                version=Wallet.version + 1,
            )
            .returning(Wallet.available)
        )
        return self.db.scalar(stmt)

    def unfreeze(self, user_id: int, amount: Decimal) -> Decimal | None:
        """解冻：frozen -= amount（frozen >= amount 才成功）。返回更新后的 frozen，不足返回 None。"""
        stmt = (
            update(Wallet)
            .where(Wallet.user_id == user_id, Wallet.frozen >= amount)
            .values(frozen=Wallet.frozen - amount, version=Wallet.version + 1)
            .returning(Wallet.frozen)
        )
        return self.db.scalar(stmt)

    def credit(self, user_id: int, amount: Decimal) -> Decimal | None:
        """入账：available += amount, total_income += amount。返回更新后的 available。"""
        stmt = (
            update(Wallet)
            .where(Wallet.user_id == user_id)
            .values(
                available=Wallet.available + amount,
                total_income=Wallet.total_income + amount,
                version=Wallet.version + 1,
            )
            .returning(Wallet.available)
        )
        return self.db.scalar(stmt)

    def refund(self, user_id: int, amount: Decimal) -> Decimal | None:
        """退款：frozen -= amount, available += amount（frozen >= amount 才成功）。

        返回更新后的 available，不足返回 None。
        """
        stmt = (
            update(Wallet)
            .where(Wallet.user_id == user_id, Wallet.frozen >= amount)
            .values(
                frozen=Wallet.frozen - amount,
                available=Wallet.available + amount,
                version=Wallet.version + 1,
            )
            .returning(Wallet.available)
        )
        return self.db.scalar(stmt)
