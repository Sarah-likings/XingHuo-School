"""统一响应构造器：成功、分页两种标准结构。

结构固定为 `{code, msg, data}`；列表 data 统一 `{items, page, page_size, total}`。
"""

from typing import Any

from app.core.enums import ErrorCode


def success(data: Any = None, msg: str = "成功") -> dict[str, Any]:
    return {"code": ErrorCode.OK.value, "msg": msg, "data": data}


def paginated(items: list[Any], page: int, page_size: int, total: int) -> dict[str, Any]:
    return success(
        data={"items": items, "page": page, "page_size": page_size, "total": total},
    )
