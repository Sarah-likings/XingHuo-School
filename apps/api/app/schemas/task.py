"""任务出入参 schema。"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import TaskCategory


class TaskCreateRequest(BaseModel):
    category: TaskCategory
    title: str = Field(min_length=4, max_length=30)
    description: str = Field(min_length=10, max_length=500)
    reward: Decimal = Field(ge=Decimal("0.01"), le=Decimal("500"))
    place: str = Field(min_length=2, max_length=40)
    deadline: datetime


class ApplyRequest(BaseModel):
    note: str | None = Field(default=None, max_length=100)


class TaskListQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    category: TaskCategory | None = None
    min_reward: Decimal | None = None
    max_reward: Decimal | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    publisher_id: int
    category: str
    title: str
    description: str
    reward: Decimal
    place: str
    deadline: datetime | None
    status: str
    apply_count: int
    created_at: datetime


class TaskDetailOut(TaskOut):
    publisher_nickname: str | None
    publisher_credit_score: int | None
