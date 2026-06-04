"""应用配置——从环境变量加载所有敏感信息，不硬编码任何密钥"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ---------- AI API Keys ----------
    mimo_api_key: str = ""
    deepseek_api_key: str = ""

    # ---------- API Base URLs ----------
    mimo_base_url: str = "https://api.mimo.com/v1"  # 占位，按实际文档修改
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # ---------- 应用配置 ----------
    app_name: str = "WooStudy"
    debug: bool = True
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
        "https://woo-study.vercel.app",  # 生产环境前端域名
    ]

    # ---------- 数据库 ----------
    database_url: str = "sqlite+aiosqlite:///./woostudy.db"

    # ---------- 图片上传 ----------
    max_upload_images: int = 2
    max_image_size_mb: int = 5
    upload_dir: str = "./uploads"

    # ---------- AI 调度 ----------
    mimo_confidence_threshold: float = 0.7  # Mimo 置信度低于此值时 fallback 到 DeepSeek

    # ---------- Mock 模式 ----------
    mock_mode: bool = False  # True = 所有 AI 调用走 Mock，不消耗真实配额

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    """全局单例配置，首次调用时从 .env 加载"""
    return Settings()
