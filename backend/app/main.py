"""FastAPI 主入口 —— 创建 app、挂载路由、启动时建表"""
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from app.core.database import engine, Base
from app.core.auth import get_current_user
from app.api.projects import router as projects_router
from app.api.articles import router as articles_router
from app.api.chat import router as chat_router
from app.api.format import router as format_router
from app.api.auth import router as auth_router

# 静态文件目录（绝对路径，避免 CWD 依赖）
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

# 创建 FastAPI 实例
app = FastAPI(
    title="AI Writer",
    description="AI 驱动的智能写作助手 — Python 版",
    version="0.2.0",
)

# CORS —— 允许前端跨域访问（以后加前端时才需要，先留着）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载认证路由（公开，不需要 token）
app.include_router(auth_router, prefix="/api")

# 挂载业务路由（统一要求登录）
auth_dep = [Depends(get_current_user)]
app.include_router(projects_router, prefix="/api", dependencies=auth_dep)
app.include_router(articles_router, prefix="/api", dependencies=auth_dep)
app.include_router(chat_router, prefix="/api", dependencies=auth_dep)
app.include_router(format_router, prefix="/api", dependencies=auth_dep)


@app.on_event("startup")
def on_startup():
    """服务启动时自动建表（开发阶段用，生产应该用 migration）"""
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    """返回前端页面（禁用缓存，确保每次拿到最新 JS）"""
    return FileResponse(
        os.path.join(_STATIC_DIR, "index.html"),
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )
