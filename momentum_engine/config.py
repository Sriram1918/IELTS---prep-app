"""
Momentum Engine Configuration
Pydantic Settings for environment variable management.
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "momentum-engine"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = Field(default="default-dev-secret-key-2024-placeholder")
    api_version: str = "v1"
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "momentum"
    postgres_password: str = "momentum_password"
    postgres_db: str = "momentum_engine"
    database_url: Optional[str] = None
    
    # Connection pool
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 10
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_url: Optional[str] = None
    redis_connection_timeout_ms: int = 200
    
    # AI Configuration
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # AI Cost Control
    ai_monthly_budget_per_user: float = 0.50
    ai_tier3_weekly_limit: int = 4
    ai_rate_limit_per_minute: int = 50
    
    # Feature Flags
    feature_laims_enabled: bool = True
    feature_cohorts_enabled: bool = True
    feature_ai_tier3_enabled: bool = True
    
    # Performance
    api_request_timeout_ms: int = 30000
    slow_query_threshold_ms: int = 1000
    
    # Monitoring
    log_level: str = "INFO"
    enable_metrics: bool = True
    
    @property
    def async_database_url(self) -> str:
        """Get async database URL for SQLAlchemy."""
        if self.database_url:
            # Convert postgresql:// to postgresql+asyncpg:// for Railway
            url = self.database_url
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def sync_database_url(self) -> str:
        """Get sync database URL for Alembic migrations."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def redis_connection_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_url:
            return self.redis_url
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()
