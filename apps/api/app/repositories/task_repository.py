"""任务数据访问。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Task)

    def page_open(
        self,
        page: int,
        page_size: int,
        category: str | None,
        min_reward,
        max_reward,
    ) -> tuple[list[Task], int]:
        """分页查询大厅可见任务（OPEN 且未删除），返回 (items, total)。"""
        stmt = select(Task).where(Task.status == "OPEN", Task.deleted_at.is_(None))
        if category is not None:
            stmt = stmt.where(Task.category == category)
        if min_reward is not None:
            stmt = stmt.where(Task.reward >= min_reward)
        if max_reward is not None:
            stmt = stmt.where(Task.reward <= max_reward)

        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(Task.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        return items, total
