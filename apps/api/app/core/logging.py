"""结构化日志（JSON）。

日志字段规范见《技术要求》4.11：time / level / trace_id / user_id / path / code / duration_ms。
敏感信息（密码、JWT、学号、姓名、证件影像键）不得写入日志，脱敏工具见 security.py。
"""

import json
import logging
import sys
from datetime import UTC, datetime

_STRUCTURED_KEYS = ("trace_id", "user_id", "path", "code", "duration_ms")


class JsonFormatter(logging.Formatter):
    """把日志记录序列化为单行 JSON。"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "time": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in _STRUCTURED_KEYS:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    # 覆盖默认 handler，避免重复输出
    root.handlers = [handler]
