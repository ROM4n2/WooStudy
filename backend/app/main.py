"""WooStudy — FastAPI 应用入口"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.database import close_db
from app.db.migrate import init_db
from app.routers import chat, errorbook, practice, lab, analysis, settings, auth, knowledge


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化 DB，关闭时关闭 DB 连接"""
    print("[App] WooStudy 后端启动中...")
    await init_db()
    print("[App] 启动完成")
    yield
    await close_db()
    print("[App] 已关闭")


settings_inst = get_settings()

app = FastAPI(
    title=settings_inst.app_name,
    description="高中物理 AI 助学 Web 项目后端",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置（允许前端开发服务器跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_inst.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件挂载（上传的图片）
upload_dir = Path(settings_inst.upload_dir)
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# 注册路由
app.include_router(chat.router)
app.include_router(errorbook.router)
app.include_router(practice.router)
app.include_router(lab.router)
app.include_router(analysis.router)
app.include_router(settings.router)
app.include_router(auth.router)
app.include_router(knowledge.router)


@app.get("/api/health")
async def health_check() -> dict:
    """健康检查接口"""
    return {"status": "ok", "app": settings_inst.app_name, "version": "0.1.0"}
