from fastapi import APIRouter

from app.routes.songs import router as songs_router
from app.routes.stream import router as stream_router

# API 统一入口：所有业务路由都在这里集中挂载，便于维护与扩展。
router = APIRouter(prefix="/api")
router.include_router(songs_router)
router.include_router(stream_router)
