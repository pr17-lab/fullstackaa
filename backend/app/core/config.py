from pydantic_settings import BaseSettings
from pydantic import field_validator, ValidationInfo
from typing import List


class Settings(BaseSettings):
    """Application settings with comprehensive validation."""
    
    # Database Configuration
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600  # 1 hour
    
    # Security & JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Application
    APP_NAME: str = "Student Academic Tracker"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str, info: ValidationInfo) -> str:
        """Validate DATABASE_URL is a PostgreSQL connection string."""
        if not v:
            raise ValueError("DATABASE_URL must be set")
        if not v.startswith("postgresql://"):
            raise ValueError(
                "DATABASE_URL must be a PostgreSQL connection string "
                "(starts with postgresql://)"
            )
        return v
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        """Validate SECRET_KEY has minimum length for security."""
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters for security. "
                f"Got {len(v)} characters."
            )
        return v
    
    @field_validator("DB_POOL_SIZE")
    @classmethod
    def validate_pool_size(cls, v: int, info: ValidationInfo) -> int:
        """Validate pool size is reasonable."""
        if v < 1:
            raise ValueError("DB_POOL_SIZE must be at least 1")
        if v > 50:
            raise ValueError("DB_POOL_SIZE should not exceed 50 for most use cases")
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str, info: ValidationInfo) -> str:
        """Validate environment is one of allowed values."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(
                f"ENVIRONMENT must be one of {allowed}, got '{v}'"
            )
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


# Singleton instance
settings = Settings()

