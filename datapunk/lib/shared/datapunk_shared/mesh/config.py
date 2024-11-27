from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

"""
Service mesh configuration with environment variable support.

Provides configuration for:
- Service discovery via Consul
- Circuit breaker fault tolerance
- Load balancing and health checks
- Retry policies
- Monitoring and tracing

NOTE: All settings can be overridden via MESH_* environment variables
"""

class CircuitBreakerConfig(BaseModel):
    """
    Circuit breaker configuration for fault tolerance.
    
    Default values tuned for microservices:
    - max_requests: Sized for typical service throughput
    - error_threshold: Balanced between sensitivity and stability
    - reset_timeout: Allows for service recovery
    
    TODO: Add support for custom failure criteria
    """
    max_requests: int = Field(default=1000, gt=0)
    error_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    reset_timeout: float = Field(default=30.0, gt=0.0)

class LoadBalancerConfig(BaseModel):
    """
    Load balancer configuration with health monitoring.
    
    Features:
    - Multiple balancing algorithms
    - Configurable health checks
    - Automatic retry support
    
    NOTE: Health check interval impacts network traffic
    """
    algorithm: str = Field(default="round_robin")
    health_check_interval: float = Field(default=10.0, gt=0.0)
    max_retries: int = Field(default=3, ge=0)

class ServiceMeshConfig(BaseSettings):
    """
    Complete service mesh configuration with environment override support.
    
    Components:
    - Service identity and versioning
    - Consul service discovery
    - Reliability patterns
    - Monitoring configuration
    
    Environment Variables:
    All settings can be overridden using MESH_ prefix:
    MESH_SERVICE_NAME=myservice
    MESH_CONSUL_HOST=consul.local
    
    WARNING: Consul settings require matching infrastructure
    TODO: Add support for other service discovery backends
    """
    service_name: str
    service_version: str = "0.1.0"
    
    # Service Discovery via Consul
    # Default values assume local Consul agent
    consul_host: str = "consul"
    consul_port: int = 8500
    consul_dc: str = "dc1"
    
    # Reliability configurations with production-ready defaults
    circuit_breaker: CircuitBreakerConfig = CircuitBreakerConfig()
    load_balancer: LoadBalancerConfig = LoadBalancerConfig()
    
    # Retry configuration with exponential backoff
    retry_max_attempts: int = Field(default=3, gt=0)
    retry_base_delay: float = Field(default=1.0, gt=0.0)
    retry_max_delay: float = Field(default=30.0, gt=0.0)
    
    # Observability toggles for production monitoring
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    
    class Config:
        """
        Configuration metadata for environment handling.
        
        Uses MESH_ prefix to avoid variable collisions.
        Example: MESH_SERVICE_NAME sets service_name
        """
        env_prefix = "MESH_"