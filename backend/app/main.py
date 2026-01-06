"""
FastAPI 应用入口
"""
import sys
import io

# 修复Windows终端中文乱码问题
if sys.platform == 'win32':
    import os
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # 设置标准输出编码为UTF-8
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        # 如果已经是TextIOWrapper或设置失败，跳过
        pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import images

# 创建 FastAPI 应用实例
app = FastAPI(
    title="地方感地图生成 API",
    description="基于地理视觉特征的地方感地图生成系统后端API",
    version="1.0.0",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(images.router)


@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    return {
        "message": "地方感地图生成 API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["健康检查"])
async def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
