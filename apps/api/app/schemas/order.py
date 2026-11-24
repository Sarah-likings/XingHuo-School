"""订单出入参 schema。"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    employer_id: int
    taker_id: int | None
    status: str
    reward: Decimal | None
    apply_note: str | None
    assigned_at: datetime | None
    delivered_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class AppealRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=200)


class ArbitrateRequest(BaseModel):
    decision: Literal["REFUND", "SETTLE"]
    remark: str | None = Field(default=None, max_length=200)
