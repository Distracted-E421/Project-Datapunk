from pydantic_settings import BaseSettings
from typing import Optional

class BaseServiceConfig(BaseSettings):
    """Base configuration for Datapunk service mesh components
    
    Provides standardized configuration across all microservices with
    built-in environment variable validation. Uses Pydantic for type safety
    and automatic environment variable parsing.
    
    NOTE: All services must provide SERVICE_NAME and PORT
    TODO: Add SSL/TLS configuration options
    FIXME: Add validation for service name format
    """
    
    # Service Identity
    # These fields uniquely identify each service in the mesh
    SERVICE_NAME: str  # Required, no default to ensure explicit naming
    SERVICE_VERSION: str = "1.0.0"  # Semantic versioning
    
    # Network Configuration
    # NOTE: Default host allows external connections
    # TODO: Add network security configuration
    HOST: str = "0.0.0.0"  # Listen on all interfaces
    PORT: int  # Required, must be unique per service
    
    # Service Discovery
    # NOTE: Consul is required for service mesh operation
    CONSUL_HOST: str = "consul"  # Default to service name
    CONSUL_PORT: int = 8500  # Standard Consul port
    
    # Observability Settings
    # NOTE: Metrics are enabled by default for monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090  # Prometheus compatible
    
    # Cache Configuration
    # NOTE: Redis is optional but recommended for performance
    # TODO: Add connection pool settings
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None
    
    class Config:
        """Pydantic configuration
        
        NOTE: Case sensitivity matters for environment variables
        Example: SERVICE_NAME maps to SERVICE_NAME, not service_name
        """
        env_file = ".env"
        case_sensitive = True 