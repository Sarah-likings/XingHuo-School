"""健康检查路由（骨架阶段唯一实现的路由）。"""

from fastapi import APIRouter

from app.core.response import success

router = APIRouter(tags=["health"])


@router.get("/health", summary="健康检查")
def health_check() -> dict:
    return success(data={"status": "ok"})
