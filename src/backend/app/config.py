import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Echo Tours API"
    debug: bool = True
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/echo_tours"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/echo_tours"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"

    # Auth
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_public_key: Optional[str] = None

    # CORS
    cors_origins: str = "http://localhost:3000"

    # SendGrid
    sendgrid_api_key: Optional[str] = None

    # Frontend URL
    frontend_url: str = "http://localhost:3000"

    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # Static files
    static_dir: str = "static"

    model_config = {
        "env_file": ".env" if Path(".env").exists() else None,
        "env_file_encoding": "utf-8",
    }


settings = Settings()
