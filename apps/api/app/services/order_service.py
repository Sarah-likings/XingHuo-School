"""订单业务：申请接单。"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import OrderStatus, TaskStatus
from app.core.exceptions import ConflictError, DuplicateError, NotFoundError, TooManyRequestsError
from app.models.order import Order
from app.models.user import User
from app.repositories.order_repository import OrderRepository
from app.repositories.task_repository import TaskRepository


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.order_repo = OrderRepository(db)
        self.task_repo = TaskRepository(db)

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
