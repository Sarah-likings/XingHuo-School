"""评价出入参 schema。"""

from pydantic import BaseModel, ConfigDict, Field


class ReviewCreateRequest(BaseModel):
    order_id: int
    score: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=200)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    from_user: int
    to_user: int
    score: int
    comment: str | None
    is_late: bool
