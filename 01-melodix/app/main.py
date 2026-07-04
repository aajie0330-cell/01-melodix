from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.models.database import init_db
from app.helpers.api_logging import register_api_logging_middleware
from app.routes.api import router as api_router

app = FastAPI(title="01-melodix", version="1.0.0")

# 前端静态资源目录（首页、CSS、JS 都从这里提供）。
FRONTEND_DIR = Path(__file__).parent.parent / "streaming" / "frontend"


@app.on_event("startup")
def startup():
    # 服务启动时先初始化数据库结构，避免第一次请求才建表。
    init_db()


# 注册全局 API 请求/响应日志中间件。
register_api_logging_middleware(app)

# 从统一入口挂载所有 API 路由，方便集中维护。
app.include_router(api_router)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_index():
    # 提供前端主页。
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    # 健康检查接口，给监控/排查使用。
    return {"status": "ok", "app": "01-melodix"}
