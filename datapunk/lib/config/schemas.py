from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import re

"""
Configuration schemas that actually make sense

This module defines the structure for all configuration in Datapunk. Each schema
is designed to be clear, validated, and actually useful. No more guessing what 
values are allowed or dealing with cryptic validation errors.

Key Design Decisions:
- Everything is validated through Pydantic (because runtime surprises suck)
- Sensible defaults where possible (but required where it matters)
- Clear type hints (because Python can be a sneaky bastard)
- Nested configs for logical grouping

NOTE: When adding new configs, follow these patterns:
1. Group related settings into their own models
2. Use type hints for everything
3. Add clear field descriptions
4. Set reasonable defaults
5. Include validation where needed
"""

class LogLevel(str, Enum):
    """Log levels that match standard Python logging"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LoggingConfig(BaseModel):
    """
    Logging setup that won't leave you in the dark
    
    Handles both file and stdout logging with rotation and retention policies.
    Default format is JSON because parsing text logs is a pain in the ass.
    """
    level: LogLevel = Field(default=LogLevel.INFO)
    format: str = Field(default="json")
    output: str = Field(default="stdout")
    file_path: Optional[str] = None
    rotation: Optional[str] = "1 day"  # Standard rotation interval
    retention: Optional[str] = "30 days"  # Keep logs for a month by default

class SecurityConfig(BaseModel):
    """
    Security settings that don't mess around
    
    Handles encryption, JWT config, and CORS. No security through obscurity here -
    everything is explicit and validated.
    
    NOTE: SSL settings are optional but highly recommended for production
    """
    encryption_key: str = Field(..., min_length=32)  # No weak keys allowed
    jwt_secret: str = Field(..., min_length=32)  # Same for JWT
    token_expiry: int = Field(default=3600)  # 1 hour default
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
    """
    Complete service configuration that ties everything together
    
    This is the main config that services use. It includes everything from
    basic service info to detailed subsystem configs.
    
    Implementation Notes:
    - Name validation ensures K8s compatibility
    - Version follows semantic versioning
    - All subsystems have reasonable defaults
    - Security config is required (no shortcuts here)
    
    TODO: Add support for custom plugin configs
    FIXME: Make environment validation more flexible
    """
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