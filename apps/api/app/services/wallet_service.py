"""钱包业务：查询余额（只读）。"""

from sqlalchemy.orm import Session

from app.models.wallet import Wallet
from app.repositories.wallet_repository import WalletRepository


class WalletService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.wallet_repo = WalletRepository(db)

    def summary(self, user_id: int) -> Wallet:
        """查询用户钱包；不存在则懒创建（注册时已建，此处兜底）。"""
        wallet = self.wallet_repo.find_one(user_id=user_id)
        if wallet is None:
            wallet = Wallet(user_id=user_id)
            self.db.add(wallet)
            self.db.flush()
        return wallet
