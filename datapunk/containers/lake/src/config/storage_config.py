# datapunk/containers/lake/src/config/storage_config.py

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class StorageConfig(BaseSettings):
    """Configuration for Lake storage services"""
    
    # Database Settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "datapunk"
    DB_PASSWORD: str = "metro2049"
    DB_NAME: str = "datapunk_lake"
    
    # Schema Settings
    USER_SCHEMA: str = "user_data"
    IMPORT_SCHEMA: str = "imports"
    SYSTEM_SCHEMA: str = "system"
    
    # Storage Paths
    DATA_PATH: Path = Path("/var/lib/postgresql/data")
    ARCHIVE_PATH: Path = Path("/var/lib/postgresql/archive")
    
    # Vector Store Settings
    VECTOR_DIMENSION: int = 1536  # Default for OpenAI embeddings
    VECTOR_INDEX_TYPE: str = "ivfflat"
    VECTOR_LISTS: int = 100
    
    # TimescaleDB Settings
    CHUNK_TIME_INTERVAL: str = "1 day"
    RETENTION_POLICY: str = "30 days"
    
    # PostGIS Settings
    SPATIAL_REF_SYS: int = 4326  # WGS84
    
    # Cache Settings
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = True