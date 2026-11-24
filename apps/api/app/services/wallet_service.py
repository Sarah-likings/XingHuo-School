"""钱包业务：余额查询、冻结、结算、退款（资金动作 + 流水）。"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.enums import FundFlowType
from app.core.exceptions import InsufficientBalanceError
from app.models.order import Order
from app.models.wallet import Wallet
from app.repositories.fund_flow_repository import FundFlowRepository
from app.repositories.wallet_repository import WalletRepository


class WalletService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.wallet_repo = WalletRepository(db)
        self.fund_flow_repo = FundFlowRepository(db)

    def summary(self, user_id: int) -> Wallet:
        """查询用户钱包；不存在则懒创建（注册时已建，此处兜底）。"""
        wallet = self.wallet_repo.find_one(user_id=user_id)
        if wallet is None:
            wallet = Wallet(user_id=user_id)
            self.db.add(wallet)
            self.db.flush()
        return wallet

    def freeze(self, user_id: int, amount: Decimal, order_id: int) -> None:
        """冻结赏金：条件更新 + 写 FREEZE 流水。余额不足抛 402。"""
        balance_after = self.wallet_repo.freeze(user_id, amount)
        if balance_after is None:
            raise InsufficientBalanceError("可用余额不足")
        self.fund_flow_repo.insert(
            user_id, order_id, FundFlowType.FREEZE.value, amount, balance_after
        )

    def settle(self, order: Order) -> None:
        """验收打款：解冻雇主 + 入账接单者 + 写 SETTLE 流水。"""
        amount = order.reward
        taker_id = order.taker_id
        if amount is None or taker_id is None:
            raise InsufficientBalanceError("订单资金信息不完整")
        if self.wallet_repo.unfreeze(order.employer_id, amount) is None:
            raise InsufficientBalanceError("冻结金额不足")
        taker_balance = self.wallet_repo.credit(taker_id, amount)
        if taker_balance is None:
            raise InsufficientBalanceError("接单者账户不存在")
        self.fund_flow_repo.insert(
            taker_id, order.id, FundFlowType.SETTLE.value, amount, taker_balance
        )

    def refund(self, order: Order, remark: str | None = None) -> None:
        """退款：解冻退回雇主 + 写 REFUND 流水。未冻结则无资金动作。"""
        amount = order.reward
        if amount is None:
            return
        balance_after = self.wallet_repo.refund(order.employer_id, amount)
        if balance_after is None:
            raise InsufficientBalanceError("冻结金额不足")
        self.fund_flow_repo.insert(
            order.employer_id, order.id, FundFlowType.REFUND.value, amount, balance_after, remark
        )
