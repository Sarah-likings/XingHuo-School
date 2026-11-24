"""资金流水数据访问（只增不改）。"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.fund_flow import FundFlow
from app.repositories.base import BaseRepository


class FundFlowRepository(BaseRepository[FundFlow]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, FundFlow)

    def insert(
        self,
        user_id: int,
        order_id: int | None,
        type_: str,
        amount: Decimal,
        balance_after: Decimal,
        remark: str | None = None,
    ) -> FundFlow:
        flow = FundFlow(
            user_id=user_id,
            order_id=order_id,
            type=type_,
            amount=amount,
            balance_after=balance_after,
            remark=remark,
        )
        self.db.add(flow)
        return flow
