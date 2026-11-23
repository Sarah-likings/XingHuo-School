"""钱包数据访问。"""

from sqlalchemy.orm import Session

from app.models.wallet import Wallet
from app.repositories.base import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Wallet)
