"""订单数据访问（申请记录与成交订单同表）。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import OrderStatus
from app.models.order import Order
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Order)

    def find_active_apply(self, task_id: int, taker_id: int) -> Order | None:
        """查同一任务同一申请人的有效申请（OPEN 行）。"""
        return self.db.scalar(
            select(Order).where(
                Order.task_id == task_id,
                Order.taker_id == taker_id,
                Order.status == OrderStatus.OPEN.value,
            )
        )

    def count_active_apply(self, task_id: int) -> int:
        """统计某任务的有效申请人数。"""
        stmt = (
            select(func.count())
            .select_from(Order)
            .where(Order.task_id == task_id, Order.status == OrderStatus.OPEN.value)
        )
        return self.db.scalar(stmt) or 0
