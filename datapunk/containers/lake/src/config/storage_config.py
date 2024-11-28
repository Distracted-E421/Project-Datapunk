# datapunk/containers/lake/src/config/storage_config.py

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

# Storage configuration for Lake service
# Manages database and file storage settings with data sovereignty focus
# Part of the Core Services layer (see sys-arch.mmd)

class StorageConfig(BaseSettings):
    """
    Configuration for Lake storage services with data sovereignty controls
    
    Manages database connections, schema organization, and storage paths
    while ensuring user data ownership and privacy requirements.
    
    NOTE: Default values should be overridden in production
    FIXME: Add encryption configuration options
    """
    
    # Database Settings
    # Default localhost for development; override for production
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "datapunk"  # Restricted privileges user
    DB_PASSWORD: str = "metro2049"  # Override via environment
    DB_NAME: str = "datapunk_lake"
    
    # Schema Settings for data isolation and access control
    USER_SCHEMA: str = "user_data"     # Personal user data storage
    IMPORT_SCHEMA: str = "imports"      # Temporary import staging
    SYSTEM_SCHEMA: str = "system"       # System metadata and configs
    
    # Storage Paths with data sovereignty considerations
    # Ensures user data remains under their control
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