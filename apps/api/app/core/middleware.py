"""请求中间件：trace_id 注入与透传、请求日志（脱敏）。

规范见《技术要求》4.11：入口生成 trace_id，透传到响应头 `X-Trace-Id`；
结构化日志落 trace_id / user_id / path / code / duration_ms，不落敏感字段。
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.request")


class TraceContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or uuid.uuid4().hex
        request.state.trace_id = trace_id

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers["X-Trace-Id"] = trace_id
        logger.info(
            "request",
            extra={
                "trace_id": trace_id,
                "user_id": getattr(request.state, "user_id", None),
                "path": request.url.path,
                "code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
