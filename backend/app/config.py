"""
应用配置模块
"""
import os
import sys
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent
WORKSPACE_DIR = PROJECT_DIR.parent


class Settings(BaseSettings):
    """应用配置"""

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # CORS 配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # 图片处理配置
    REQUEST_TIMEOUT: int = 15
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
    MAX_IMAGE_SIZE: int = 2048

    # Place search configuration
    AMAP_WEB_SERVICE_KEY: str = ""
    PLACE_SEARCH_PROVIDER: str = "auto"
    PLACE_SEARCH_TIMEOUT: int = 8

    # 外部脚本配置（Day3）
    PIPELINE_PYTHON_EXE: str = sys.executable
    SHADOW_SCRIPT_PATH: str = str(PROJECT_DIR / "code.py")
    ONEFORMER_SCRIPT_PATH: str = str(WORKSPACE_DIR / "OneFormer" / "hf_cityscapes_one_image_semantic.py")
    ONEFORMER_MODEL_DIR: str = str(WORKSPACE_DIR / "models" / "oneformer_cityscapes_swin_large")
    ONEFORMER_LOCAL_FILES_ONLY: bool = True
    ONEFORMER_DEVICE: str = "cuda"


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()
