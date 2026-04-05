from typing import List

from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600  # seconds (1 hour)

    # Security & JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Application
    APP_NAME: str = "Student Academic Tracker"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ML sub-service (internal only — not exposed publicly)
    ML_SERVICE_URL: str = "http://localhost:8001"
    ML_SERVICE_TIMEOUT: float = 3.0  # seconds before falling back to built-in bank

    # External APIs
    RAPIDAPI_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Pydantic v2 settings config
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # ---------------------------------------------------------------------------
    # Validators
    # ---------------------------------------------------------------------------

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str, info: ValidationInfo) -> str:
        if not v:
            raise ValueError("DATABASE_URL must be set")
        if not v.startswith("postgresql://"):
            raise ValueError(
                "DATABASE_URL must be a PostgreSQL connection string (starts with postgresql://)"
            )
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        if len(v) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters for security. Got {len(v)} characters."
            )
        return v

    @field_validator("DB_POOL_SIZE")
    @classmethod
    def validate_pool_size(cls, v: int, info: ValidationInfo) -> int:
        if v < 1:
            raise ValueError("DB_POOL_SIZE must be at least 1")
        if v > 50:
            raise ValueError("DB_POOL_SIZE should not exceed 50 for most use cases")
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str, info: ValidationInfo) -> str:
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}, got '{v}'")
        return v


# Singleton instance
settings = Settings()
