"""FastAPI 应用入口：中间件、异常处理器、路由注册。"""

from fastapi import FastAPI

from app.core.exception_handlers import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import TraceContextMiddleware
from app.routers import api_router


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        title="星火校园 API",
        version="0.1.0",
        description="星火校园任务互助平台后端接口（FastAPI + SQLAlchemy + PostgreSQL）",
    )
    app.add_middleware(TraceContextMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
