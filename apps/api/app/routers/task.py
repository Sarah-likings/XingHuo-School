"""任务路由：发布、大厅列表、详情、申请接单。"""

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_verified
from app.core.response import paginated, success
from app.models.user import User
from app.schemas.task import ApplyRequest, TaskCreateRequest, TaskDetailOut, TaskListQuery, TaskOut
from app.services.order_service import OrderService
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", status_code=201, summary="发布任务")
def create_task(
    data: TaskCreateRequest,
    user: User = Depends(require_verified),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    task = TaskService(db).create(user, data, idempotency_key)
    return success(data=TaskOut.model_validate(task).model_dump())


@router.get("", summary="任务大厅列表")
def list_tasks(query: TaskListQuery = Depends(), db: Session = Depends(get_db)) -> dict:
    items, total = TaskService(db).page(query)
    return paginated(
        [TaskOut.model_validate(t).model_dump() for t in items],
        query.page,
        query.page_size,
        total,
    )


@router.get("/{task_id}", summary="任务详情")
def get_task(task_id: int, db: Session = Depends(get_db)) -> dict:
    task, publisher = TaskService(db).detail(task_id)
    data = TaskDetailOut(
        **TaskOut.model_validate(task).model_dump(),
        publisher_nickname=publisher.nickname if publisher else None,
        publisher_credit_score=publisher.credit_score if publisher else None,
    )
    return success(data=data.model_dump())


@router.post("/{task_id}/apply", status_code=201, summary="申请接单")
def apply_task(
    task_id: int,
    data: ApplyRequest,
    user: User = Depends(require_verified),
    db: Session = Depends(get_db),
) -> dict:
    order = OrderService(db).apply(user, task_id, data.note)
    return success(data={"order_id": order.id, "task_id": task_id, "status": order.status})
