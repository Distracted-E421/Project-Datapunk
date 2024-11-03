from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Datapunk Stream"
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # RabbitMQ
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = "guest"
    
    # PostgreSQL
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Temporal
    TEMPORAL_HOST: str = "localhost"
    TEMPORAL_PORT: int = 7233
    
    # Prefect
    PREFECT_API_URL: Optional[str] = None
    
    # YouTube API Settings
    YOUTUBE_API_KEY: str
    YOUTUBE_CLIENT_ID: str
    YOUTUBE_CLIENT_SECRET: str
    YOUTUBE_QUOTA_LIMIT: int = 10000  # Daily quota limit
    
    # Play Store API Settings
    PLAY_STORE_API_KEY: str
    PLAY_STORE_DAILY_QUOTA: int = 10000  # Default daily quota
    PLAY_STORE_BATCH_SIZE: int = 20
    PLAY_STORE_MAX_LIBRARY_SIZE: int = 1000
    
    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
