"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "SupportIQ"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = Field(default="dev-secret-change-in-production-32chars")
    app_api_prefix: str = "/api/v1"
    app_cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "supportiq"
    postgres_password: str = "supportiq_secret"
    postgres_db: str = "supportiq"
    database_url: str = "postgresql+asyncpg://supportiq:supportiq_secret@localhost:5432/supportiq"
    database_url_sync: str = "postgresql://supportiq:supportiq_secret@localhost:5432/supportiq"

    # MongoDB
    mongo_url: str = "mongodb://localhost:27017/supportiq_events"
    mongo_db: str = "supportiq_events"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # JWT
    jwt_secret_key: str = Field(default="jwt-dev-secret-change-me-to-long-random-string")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # AI
    llm_provider: str = "mock"  # mock | openai
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    embedding_provider: str = "mock"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.65
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 150

    # Files
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 20
    allowed_upload_extensions: str = ".pdf,.docx,.txt,.md,.csv,.html"

    # Email
    email_provider: str = "mock"
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: str = "noreply@supportiq.local"

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_ai_per_minute: int = 20

    # Observability
    log_level: str = "INFO"
    enable_metrics: bool = True

    # Multi-tenancy
    enable_tenant_isolation: bool = True
    default_organization_slug: str = "demo-ecommerce"

    seed_demo_data: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.app_cors_origins.split(",") if o.strip()]

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [e.strip().lower() for e in self.allowed_upload_extensions.split(",") if e.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in ("development", "dev", "local")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()