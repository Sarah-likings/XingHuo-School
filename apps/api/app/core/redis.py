"""Redis 客户端（惰性连接）。

用于任务大厅热点缓存、会话在线状态、限流计数（见《技术要求》）。
"""

from redis import Redis

from app.core.config import settings

_client: Redis | None = None


def get_redis() -> Redis:
    """返回全局 Redis 客户端，首次调用时才建立连接。"""
    global _client
    if _client is None:
        _client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _client
