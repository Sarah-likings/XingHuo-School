"""任务业务：发布、大厅列表、详情。"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import TaskStatus
from app.core.exceptions import DuplicateError, NotFoundError, ValidationFailedError
from app.core.idempotency import try_acquire
from app.models.audit_log import AuditLog
from app.models.task import Task
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreateRequest, TaskListQuery

# 简化的违规词表（后续可换配置表/数据库）
_SENSITIVE_WORDS = ("代考", "代写", "刷单", "赌博")


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.task_repo = TaskRepository(db)

    def create(self, user: User, data: TaskCreateRequest, idem_key: str | None) -> Task:
        """发布任务：幂等 + 时限校验 + 违规词 + 判重 + 建 task + 审计。"""
        if idem_key and not try_acquire(idem_key):
            raise DuplicateError("重复提交，请勿重复操作")

        deadline = data.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        if deadline <= datetime.now(UTC) + timedelta(hours=1):
            raise ValidationFailedError("截止时间需晚于当前 1 小时")

        hit = self._scan_word(data.title + data.description)
        if hit:
            raise ValidationFailedError(f"内容含违规词：{hit}")

        if self._is_duplicate(user.id, data.title):
            raise DuplicateError("10 分钟内重复发布相同任务")

        task = Task(
            publisher_id=user.id,
            category=data.category.value,
            title=data.title,
            description=data.description,
            reward=data.reward,
            place=data.place,
            deadline=deadline,
            status=TaskStatus.OPEN.value,
            apply_count=0,
            ai_draft=False,
        )
        self.db.add(task)
        self.db.flush()
        self.db.add(
            AuditLog(
                actor_id=user.id,
                action="PUBLISH_TASK",
                target_type="task",
                target_id=task.id,
                detail={"category": data.category.value, "reward": str(data.reward)},
            )
        )
        return task

    def page(self, query: TaskListQuery) -> tuple[list[Task], int]:
        """大厅列表：分页 + 筛选。"""
        return self.task_repo.page_open(
            query.page,
            query.page_size,
            query.category.value if query.category else None,
            query.min_reward,
            query.max_reward,
        )

    def detail(self, task_id: int) -> tuple[Task, User | None]:
        """任务详情：返回任务与雇主（用于公开标签）。"""
        task = self.task_repo.get(task_id)
        if task is None or task.deleted_at is not None:
            raise NotFoundError("任务不存在或已下架")
        publisher = self.db.get(User, task.publisher_id)
        return task, publisher

    def _scan_word(self, text: str) -> str | None:
        for word in _SENSITIVE_WORDS:
            if word in text:
                return word
        return None

    def _is_duplicate(self, publisher_id: int, title: str) -> bool:
        """简化判重：同雇主 10 分钟内同标题（Jaccard 相似度 TODO）。"""
        cutoff = datetime.now(UTC) - timedelta(minutes=10)
        stmt = (
            select(func.count())
            .select_from(Task)
            .where(
                Task.publisher_id == publisher_id,
                Task.title == title,
                Task.created_at >= cutoff,
            )
        )
        return (self.db.scalar(stmt) or 0) > 0
