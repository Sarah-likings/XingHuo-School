"""通用出入参 schema（分页参数等）。业务 schema 在 W3-W4 认证实现时补充。"""

from pydantic import BaseModel, Field


class PageParams(BaseModel):
    """列表接口统一分页参数：page 从 1 起，page_size 默认 20、上限 100。"""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
