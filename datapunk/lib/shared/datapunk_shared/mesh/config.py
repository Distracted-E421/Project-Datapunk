from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration"""
    max_requests: int = Field(default=1000, gt=0)
    error_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    reset_timeout: float = Field(default=30.0, gt=0.0)

class LoadBalancerConfig(BaseModel):
    """Load balancer configuration"""
    algorithm: str = Field(default="round_robin")
    health_check_interval: float = Field(default=10.0, gt=0.0)
    max_retries: int = Field(default=3, ge=0)

class ServiceMeshConfig(BaseSettings):
    """Service mesh configuration"""
    service_name: str
    service_version: str = "0.1.0"
    
    # Service Discovery
    consul_host: str = "consul"
    consul_port: int = 8500
    consul_dc: str = "dc1"
    
    # Circuit Breaker
    circuit_breaker: CircuitBreakerConfig = CircuitBreakerConfig()
    
    # Load Balancer
    load_balancer: LoadBalancerConfig = LoadBalancerConfig()
    
    # Retry Configuration
    retry_max_attempts: int = Field(default=3, gt=0)
    retry_base_delay: float = Field(default=1.0, gt=0.0)
    retry_max_delay: float = Field(default=30.0, gt=0.0)
    
    # Monitoring
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    
    class Config:
        env_prefix = "MESH_" 