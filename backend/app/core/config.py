from pydantic_settings import BaseSettings
import os
from enum import Enum
from typing import List

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI-Powered API Security System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Database
    DATABASE_URL: str="postgresql+asyncpg://postgres:5501@localhost:5513/api_security"

    # Redis
    REDIS_URL:str="redis://localhost:6379"

    # JWT Authentication (NEW)
    JWT_SECRET_KEY: str = "your_64_char_hex_secret_key_here"  # Default fallback, override in .env
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_EXPIRE_MINUTES: int = 15
    BCRYPT_ROUNDS: int = 12
    MAX_FAILED_LOGIN_ATTEMPTS: int = 10
    ACCOUNT_LOCKOUT_MINUTES: int = 30

    # Security
    RATE_LIMIT_WINDOW: int = 60
    MAX_REQUESTS_PER_MINUTE: int = 100

    # Block durations
    BLOCK_SOFT_DURATION: int = 120
    BLOCK_MEDIUM_DURATION: int = 600
    BLOCK_HARD_DURATION: int = 3600

    # Logging
    LOG_LEVEL: str = "INFO"

    # Feature thresholds
    HIGH_REQUEST_THRESHOLD: int = 50
    HIGH_RATIO_THRESHOLD: float = 0.8
    HIGH_ENTROPY_THRESHOLD: float = 0.7

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "../../../.env")
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()