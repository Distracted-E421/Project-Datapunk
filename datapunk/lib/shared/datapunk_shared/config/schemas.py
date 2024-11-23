from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import re

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: LogLevel = Field(default=LogLevel.INFO)
    format: str = Field(default="json")
    output: str = Field(default="stdout")
    file_path: Optional[str] = None
    rotation: Optional[str] = "1 day"
    retention: Optional[str] = "30 days"

class SecurityConfig(BaseModel):
    """Security configuration"""
    encryption_key: str = Field(..., min_length=32)
    jwt_secret: str = Field(..., min_length=32)
    token_expiry: int = Field(default=3600)  # seconds
    allowed_origins: List[str] = Field(default=["*"])
    ssl_enabled: bool = Field(default=True)
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None

class CacheConfig(BaseModel):
    """Cache configuration"""
    enabled: bool = Field(default=True)
    backend: str = Field(default="redis")
    ttl: int = Field(default=300)  # seconds
    max_size: str = Field(default="1GB")
    eviction_policy: str = Field(default="lru")

class MetricsConfig(BaseModel):
    """Metrics configuration"""
    enabled: bool = Field(default=True)
    interval: int = Field(default=60)  # seconds
    retention_days: int = Field(default=30)
    exporters: List[str] = Field(default=["prometheus"])

class TracingConfig(BaseModel):
    """Tracing configuration"""
    enabled: bool = Field(default=True)
    sampler_type: str = Field(default="probabilistic")
    sampling_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    exporter: str = Field(default="jaeger")

class ResourceLimits(BaseModel):
    """Resource limits configuration"""
    cpu_limit: str = Field(default="1.0")
    memory_limit: str = Field(default="2Gi")
    storage_limit: str = Field(default="10Gi")
    max_connections: int = Field(default=1000)
    max_file_descriptors: int = Field(default=65535)

class ServiceConfig(BaseModel):
    """Extended service configuration"""
    name: str
    version: str = Field(default="0.1.0")
    host: str
    port: int = Field(ge=1, le=65535)
    environment: str
    logging: LoggingConfig = LoggingConfig()
    security: SecurityConfig
    cache: CacheConfig = CacheConfig()
    metrics: MetricsConfig = MetricsConfig()
    tracing: TracingConfig = TracingConfig()
    resources: ResourceLimits = ResourceLimits()
    
    @validator('name')
    def validate_service_name(cls, v):
        if not re.match(r'^[a-z][a-z0-9-]*$', v):
            raise ValueError(
                'Service name must start with a letter and contain only '
                'lowercase letters, numbers, and hyphens'
            )
        return v
    
    @validator('version')
    def validate_version(cls, v):
        if not re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$', v):
            raise ValueError('Invalid version format')
        return v

class BackupConfig(BaseModel):
    """Backup configuration"""
    enabled: bool = Field(default=True)
    schedule: str = Field(default="0 0 * * *")  # cron format
    retention_count: int = Field(default=7)
    storage_path: str = Field(default="/backups")
    compression: bool = Field(default=True)
    encryption: bool = Field(default=True)

class MaintenanceConfig(BaseModel):
    """Maintenance configuration"""
    enabled: bool = Field(default=True)
    window_start: str = Field(default="00:00")
    window_duration: int = Field(default=120)  # minutes
    auto_vacuum: bool = Field(default=True)
    auto_analyze: bool = Field(default=True)

class FeatureFlags(BaseModel):
    """Feature flags configuration"""
    experimental_features: bool = Field(default=False)
    beta_features: bool = Field(default=False)
    debug_mode: bool = Field(default=False)
    maintenance_mode: bool = Field(default=False)

class GlobalConfig(BaseModel):
    """Complete global configuration"""
    environment: str
    timezone: str = Field(default="UTC")
    database: DatabaseConfig
    redis: RedisConfig
    service_ports: ServicePorts
    monitoring: MonitoringConfig
    logging: LoggingConfig = LoggingConfig()
    security: SecurityConfig
    backup: BackupConfig = BackupConfig()
    maintenance: MaintenanceConfig = MaintenanceConfig()
    features: FeatureFlags = FeatureFlags()
    
    class Config:
        validate_assignment = True
        extra = "forbid"