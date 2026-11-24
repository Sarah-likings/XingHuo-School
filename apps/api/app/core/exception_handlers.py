"""全局异常处理器：把各类异常转成统一响应 `{code, msg, data}`。

- AppError 子类 → 各自的 code / http_status；
- RequestValidationError → 422 VALIDATION_FAILED；
- StarletteHTTPException → 按状态码映射错误码；
- 其余 Exception → 500 INTERNAL_ERROR，不向客户端暴露堆栈。
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.enums import ErrorCode
from app.core.exceptions import AppError


def _error_response(code: str, msg: str, status_code: int, trace_id: str | None) -> JSONResponse:
    headers = {"X-Trace-Id": trace_id} if trace_id else None
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "msg": msg, "data": None},
        headers=headers,
    )


def _trace_id(request: Request) -> str | None:
    return getattr(request.state, "trace_id", None)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.code, exc.msg, exc.http_status, _trace_id(request))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _error_response(
            ErrorCode.VALIDATION_FAILED.value,
            "请求参数校验失败",
            422,
            _trace_id(request),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _map_http_code(exc.status_code)
        return _error_response(code, str(exc.detail), exc.status_code, _trace_id(request))

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(
            ErrorCode.INTERNAL_ERROR.value,
            "服务异常，请稍后再试",
            500,
            _trace_id(request),
        )


def _map_http_code(status_code: int) -> str:
    """把 Starlette 默认 HTTP 状态码映射到业务错误码。"""
    mapping = {
        401: ErrorCode.UNAUTHORIZED.value,
        403: ErrorCode.FORBIDDEN.value,
        404: ErrorCode.NOT_FOUND.value,
        405: ErrorCode.BAD_REQUEST.value,
        429: ErrorCode.TOO_MANY_REQUESTS.value,
    }
    return mapping.get(status_code, ErrorCode.INTERNAL_ERROR.value)
