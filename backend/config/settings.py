"""Pydantic settings — ENV-based configuration."""

from pathlib import Path

from pydantic import ConfigDict, Field, PrivateAttr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Vacancy-Search"
    APP_ENV: str = "development"
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vacancy_search"

    # MinIO
    MINIO_URL: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "knowledge"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = "test-client-id"
    GOOGLE_CLIENT_SECRET: str = ""

    # JWT (RS256)
    JWT_PRIVATE_KEY: str | Path = ""
    JWT_PUBLIC_KEY: str | Path = ""
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Security
    SECRET_KEY: str = "dev-secret-key"

    # LLM API key encryption (Fernet)
    LLM_ENCRYPTION_KEY: str = "basetest1234567890basetest1234567890bA=="

    _cli_parse_args: PrivateAttr = PrivateAttr(default=None)

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Module-level singleton for direct imports
settings = Settings()


def get_settings() -> Settings:
    """Return fresh settings (useful for tests)."""
    return Settings()
