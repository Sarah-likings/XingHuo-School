"""幂等键（C6 组件简化实现）。

写接口凡可能被重复触发的（发布任务），请求头携带 `Idempotency-Key`（前端生成 UUID），
服务端 24 小时内同键拒绝重复提交。Redis 不可用时降级为不幂等（可用性优先）。
"""

import logging

from app.core.redis import get_redis

logger = logging.getLogger("app.idempotency")

_IDEM_TTL_SECONDS = 24 * 60 * 60


def try_acquire(key: str) -> bool:
    """尝试获取幂等键（SETNX）。首次返回 True，已存在返回 False。"""
    try:
        return bool(get_redis().set(f"idem:{key}", "1", nx=True, ex=_IDEM_TTL_SECONDS))
    except Exception as exc:  # noqa: BLE001 —— Redis 不可用降级为不幂等
        logger.warning("幂等键获取失败，降级为不幂等: %s", exc)
        return True
