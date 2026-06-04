"""应用配置——从环境变量加载所有敏感信息，不硬编码任何密钥"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ---------- AI API Keys（备选：当用户未提供自己的 Key 时使用） ----------
    mimo_api_key: str = ""
    deepseek_api_key: str = ""

    # ---------- API Base URLs ----------
    mimo_base_url: str = "https://api.xiaomimimo.com/v1"
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # ---------- 应用配置 ----------
    app_name: str = "WooStudy"
    debug: bool = True
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
        "https://woo-study.vercel.app",
    ]

    # ---------- 数据库 ----------
    database_url: str = "sqlite+aiosqlite:///./woostudy.db"

    # ---------- 图片上传 ----------
    max_upload_images: int = 2
    max_image_size_mb: int = 5
    upload_dir: str = "./uploads"

    # ---------- AI 调度 ----------
    mimo_confidence_threshold: float = 0.7

    # ---------- Mock 模式 ----------
    mock_mode: bool = False

    # ---------- JWT ----------
    jwt_secret: str = "dev-secret-change-in-production"

    # ---------- Mimo 邀请码 ----------
    mimo_invite_code: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    """全局单例配置，首次调用时从 .env 加载"""
    return Settings()
