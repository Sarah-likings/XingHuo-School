"""路由聚合：统一挂载到 `/api` 前缀下。"""

from fastapi import APIRouter

from app.routers import admin, auth, health, verify

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(verify.router)
api_router.include_router(admin.router)
