"""订单业务：申请接单、选定冻结、状态迁移、交付、验收。"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import OrderStatus, TaskStatus
from app.core.exceptions import (
    ConflictError,
    DuplicateError,
    ForbiddenError,
    NotFoundError,
    TaskTakenError,
    TooManyRequestsError,
)
from app.core.idempotency import try_acquire
from app.core.state_machine import can_transition
from app.models.order import Order
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.repositories.task_repository import TaskRepository
from app.services.wallet_service import WalletService


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.task_repo = TaskRepository(db)
        self.wallet_service = WalletService(db)

    def apply(self, user: User, task_id: int, note: str | None) -> Order:
        """申请接单：任务 OPEN + 非本人 + 未重复 + 人数未满。"""
        task = self.task_repo.get(task_id)
        if task is None or task.deleted_at is not None:
            raise NotFoundError("任务不存在或已下架")
        if task.status != TaskStatus.OPEN.value:
            raise ConflictError("任务已不可申请")
        if task.publisher_id == user.id:
            raise ConflictError("不能申请自己发布的任务")
        if self.order_repo.find_active_apply(task_id, user.id):
            raise DuplicateError("已申请过该任务")
        if self.order_repo.count_active_apply(task_id) >= settings.task_apply_limit:
            raise TooManyRequestsError("申请人数已满")

        order = Order(
            task_id=task_id,
            employer_id=task.publisher_id,
            taker_id=user.id,
            status=OrderStatus.OPEN.value,
            apply_note=note,
        )
        task.apply_count += 1
        self.db.add(order)
        self.db.flush()
        # 通知雇主 TODO（后续接消息模块 C4）
        return order

    def assign(self, user: User, order_id: int, idem_key: str | None = None) -> Order:
        """选定接单人并冻结赏金（P0402）：两处 CAS + 单一事务。"""
        if idem_key and not try_acquire(idem_key):
            raise DuplicateError("重复提交，请勿重复操作")
        order = self.order_repo.get(order_id)
        if order is None or order.deleted_at is not None:
            raise NotFoundError("订单不存在")
        if order.employer_id != user.id:
            raise ForbiddenError("仅雇主可选定接单人")
        if order.status != OrderStatus.OPEN.value:
            raise TaskTakenError("该订单已不可选定")

        task = self.task_repo.get(order.task_id)
        if task is None:
            raise NotFoundError("任务不存在")
        reward = task.reward

        # CAS 选定：写入冻结金额快照 + 选定时间
        rows = self.order_repo.cas_status(
            order_id,
            OrderStatus.OPEN.value,
            OrderStatus.ASSIGNED.value,
            reward=reward,
            assigned_at=datetime.now(UTC),
        )
        if rows != 1:
            raise TaskTakenError("该任务已被其他同学接走")

        # CAS 冻结（同一事务，失败整体回滚）
        self.wallet_service.freeze(user.id, reward, order_id)

        # 写事件 + 其余申请失效
        self.order_repo.add_event(
            order_id, OrderStatus.OPEN.value, OrderStatus.ASSIGNED.value, user.id
        )
        self.order_repo.cancel_others(order.task_id, order.taker_id)
        order.status = OrderStatus.ASSIGNED.value
        order.reward = reward
        # 通知 TODO（后续接消息模块 C4）
        return order

    def deliver(self, user: User, order_id: int) -> Order:
        """交付（接单者）：ASSIGNED → DELIVERED。"""
        order = self._get_order(order_id)
        if order.taker_id != user.id:
            raise ForbiddenError("仅接单者可交付")
        self.transition(order, OrderStatus.DELIVERED.value, user.id, delivered_at=datetime.now(UTC))
        return order

    def accept(self, user: User, order_id: int, idem_key: str | None = None) -> Order:
        """验收（雇主）：DELIVERED → COMPLETED，后置打款。"""
        if idem_key and not try_acquire(idem_key):
            raise DuplicateError("重复提交，请勿重复操作")
        order = self._get_order(order_id)
        if order.employer_id != user.id:
            raise ForbiddenError("仅雇主可验收")
        self.transition(order, OrderStatus.COMPLETED.value, user.id, completed_at=datetime.now(UTC))
        return order

    def transition(
        self,
        order: Order,
        to: str,
        operator_id: int,
        remark: str | None = None,
        **extra,
    ) -> None:
        """状态机唯一入口：校验迁移 + CAS + 写事件 + 后置动作。

        禁止任何位置直接 `UPDATE "order" SET status`，一律走本方法。
        """
        frm = order.status
        if not can_transition(frm, to):
            raise ConflictError(f"不允许从 {frm} 迁移到 {to}")
        rows = self.order_repo.cas_status(order.id, frm, to, **extra)
        if rows != 1:
            raise ConflictError("订单状态已变化，请刷新")

        self.order_repo.add_event(order.id, frm, to, operator_id, remark)

        if to == OrderStatus.COMPLETED.value:
            self.wallet_service.settle(order)
        elif to == OrderStatus.REFUNDED.value:
            self.wallet_service.refund(order, remark)

        order.status = to

    def appeal(self, user: User, order_id: int, reason: str) -> Order:
        """发起申诉（双方）：ASSIGNED/DELIVERED → APPEALING。"""
        order = self._get_order(order_id)
        if order.employer_id != user.id and order.taker_id != user.id:
            raise ForbiddenError("仅订单双方可申诉")
        if order.status not in (OrderStatus.ASSIGNED.value, OrderStatus.DELIVERED.value):
            raise ConflictError("当前状态不可申诉")
        self.transition(order, OrderStatus.APPEALING.value, user.id, reason)
        return order

    def arbitrate(
        self, admin: User, order_id: int, decision: str, remark: str | None = None
    ) -> Order:
        """管理员裁决：REFUND → 退款，SETTLE → 强制结算。"""
        order = self._get_order(order_id)
        if order.status != OrderStatus.APPEALING.value:
            raise ConflictError("仅申诉中的订单可裁决")
        if decision == "REFUND":
            self.transition(order, OrderStatus.REFUNDED.value, admin.id, remark)
        else:
            self.transition(order, OrderStatus.COMPLETED.value, admin.id, remark)
        return order

    def check_overdue(self) -> int:
        """超时兜底：扫描超时未验收的 DELIVERED 订单，自动完成结算。返回处理条数。"""
        cutoff = datetime.now(UTC) - timedelta(hours=settings.order_accept_timeout_hours)
        orders = self.order_repo.find_overdue(cutoff)
        count = 0
        for order in orders:
            try:
                self.transition(order, OrderStatus.COMPLETED.value, 0, "超时自动完成")
                count += 1
            except ConflictError:
                continue  # 已被人工验收，跳过（幂等）
        return count

    def _get_order(self, order_id: int) -> Order:
        order = self.order_repo.get(order_id)
        if order is None or order.deleted_at is not None:
            raise NotFoundError("订单不存在")
        return order
