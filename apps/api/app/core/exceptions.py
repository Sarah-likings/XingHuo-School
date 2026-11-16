"""统一业务异常：AppError 基类 + 具体异常。

所有业务错误通过抛 AppError 子类表达，由 exception_handlers 转成统一响应
`{code, msg, data}`。禁止在 router/service 里直接返回错误字典。
"""

from app.core.enums import ErrorCode


class AppError(Exception):
    """业务异常基类。"""

    def __init__(
        self,
        code: ErrorCode,
        msg: str,
        http_status: int = 400,
    ) -> None:
        self.code = code.value
        self.msg = msg
        self.http_status = http_status
        super().__init__(msg)


class BadRequestError(AppError):
    def __init__(self, msg: str = "请求格式错误") -> None:
        super().__init__(ErrorCode.BAD_REQUEST, msg, 400)


class UnauthorizedError(AppError):
    def __init__(self, msg: str = "未登录或令牌过期") -> None:
        super().__init__(ErrorCode.UNAUTHORIZED, msg, 401)


class InsufficientBalanceError(AppError):
    def __init__(self, msg: str = "可用余额不足") -> None:
        super().__init__(ErrorCode.INSUFFICIENT_BALANCE, msg, 402)


class ForbiddenError(AppError):
    def __init__(self, msg: str = "无权限执行该操作") -> None:
        super().__init__(ErrorCode.FORBIDDEN, msg, 403)


class NotVerifiedError(AppError):
    def __init__(self, msg: str = "完成实名认证后才能进行该操作") -> None:
        super().__init__(ErrorCode.NOT_VERIFIED, msg, 403)


class NotFoundError(AppError):
    def __init__(self, msg: str = "资源不存在或已下架") -> None:
        super().__init__(ErrorCode.NOT_FOUND, msg, 404)


class ConflictError(AppError):
    def __init__(self, msg: str = "状态冲突，请刷新后重试") -> None:
        super().__init__(ErrorCode.CONFLICT, msg, 409)


class TaskTakenError(AppError):
    def __init__(self, msg: str = "该任务已被其他同学接走") -> None:
        super().__init__(ErrorCode.TASK_TAKEN, msg, 409)


class DuplicateError(AppError):
    def __init__(self, msg: str = "重复提交") -> None:
        super().__init__(ErrorCode.DUPLICATE, msg, 409)


class ValidationFailedError(AppError):
    def __init__(self, msg: str = "字段校验失败") -> None:
        super().__init__(ErrorCode.VALIDATION_FAILED, msg, 422)


class TooManyRequestsError(AppError):
    def __init__(self, msg: str = "请求过于频繁，请稍后再试") -> None:
        super().__init__(ErrorCode.TOO_MANY_REQUESTS, msg, 429)
