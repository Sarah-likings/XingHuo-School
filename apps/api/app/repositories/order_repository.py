"""订单数据访问（申请记录与成交订单同表）。"""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.enums import OrderStatus
from app.models.order import Order
from app.models.order_event import OrderEvent
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

    def cas_status(self, order_id: int, frm: str, to: str, **extra) -> int:
        """条件更新订单状态（CAS），返回影响行数（1 成功 / 0 失败）。"""
        stmt = (
            update(Order)
            .where(Order.id == order_id, Order.status == frm)
            .values(status=to, **extra)
        )
        return self.db.execute(stmt).rowcount

    def add_event(
        self,
        order_id: int,
        frm: str,
        to: str,
        operator_id: int | None,
        remark: str | None = None,
    ) -> None:
        """写一条状态迁移事件（履约证据链，只增不改）。"""
        self.db.add(
            OrderEvent(
                order_id=order_id,
                from_status=frm,
                to_status=to,
                operator_id=operator_id,
                remark=remark,
            )
        )

    def cancel_others(self, task_id: int, taker_id: int) -> None:
        """选定接单人后，其余申请行置 CANCELLED。"""
        self.db.execute(
            update(Order)
            .where(
                Order.task_id == task_id,
                Order.status == OrderStatus.OPEN.value,
                Order.taker_id != taker_id,
            )
            .values(status=OrderStatus.CANCELLED.value)
        )

    def find_overdue(self, cutoff: datetime) -> list[Order]:
        """查已交付且超过截止时间未验收的订单（超时兜底）。"""
        return list(
            self.db.scalars(
                select(Order).where(
                    Order.status == OrderStatus.DELIVERED.value,
                    Order.delivered_at < cutoff,
                )
            )
        )
