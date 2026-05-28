from pydantic_settings import BaseSettings
from typing import List, Optional
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class Settings(BaseSettings):
    #Application
    APP_NAME: str = "AI-Powered API Security System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True

    #SERVER
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    # CORS - Allow frontend origins
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",      # React default
        "http://localhost:5173",      # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    #Database
    DATABASE_URL: str

    #Redis
    REDIS_URL: str

    #Security
    RATE_LIMIT_WINDOW: int = 60 #seconds
    MAX_REQUESTS_PER_MINUTE: int = 100

    #Block Durations(seconds)
    BLOCK_SOFT_DURATION: int = 120 #2 minutes
    BLOCK_MEDIUM_DURATION: int = 600 #10 minutes
    BLOCK_HARD_DURATION: int = 3600 #1 hour

    #Logging
    LOG_LEVEL: str = "INFO"

    #Feature thresholds
    HIGH_REQUEST_THRESHOLD: int = 50
    HIGH_RATIO_THRESHOLD: float = 0.8
    HIGH_ENTROPY_THRESHOLD: float = 0.7

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()