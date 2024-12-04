from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

"""
Service mesh configuration validation with policy enforcement.

Provides configuration validation for:
- Load balancing strategies
- Retry policies
- Circuit breaker patterns
- Health check configurations

Uses Pydantic for runtime validation and type safety.
"""

class LoadBalancingPolicy(str, Enum):
    """
    Load balancing strategies optimized for different scenarios:
    
    ROUND_ROBIN: Even distribution, best for homogeneous services
    LEAST_CONNECTIONS: Adaptive to service capacity
    RESPONSE_TIME: Latency-sensitive routing
    RANDOM: Testing and development environments
    """
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RESPONSE_TIME = "response_time"
    RANDOM = "random"

class RetryPolicy(BaseModel):
    """
    Retry behavior configuration with exponential backoff.
    
    Key parameters:
    - max_attempts: Limits retry attempts to prevent resource exhaustion
    - base_delay: Initial delay between retries
    - max_delay: Caps exponential growth of delays
    
    NOTE: Conditions determine when retries are triggered
    TODO: Add custom retry condition support
    """
    max_attempts: int = Field(ge=1, le=10, default=3)
    base_delay: float = Field(ge=0.1, le=60.0, default=1.0)
    max_delay: float = Field(ge=1.0, le=300.0, default=30.0)
    conditions: List[str] = Field(
        default=["5xx", "connect-failure", "timeout"]
    )

class CircuitBreakerPolicy(BaseModel):
    """
    Circuit breaker configuration for fault tolerance.
    
    Features:
    - Configurable failure thresholds
    - Automatic recovery attempts
    - Rolling window for error rate calculation
    
    NOTE: window_size affects memory usage and detection speed
    """
    failure_threshold: float = Field(ge=0.0, le=1.0, default=0.5)
    reset_timeout: float = Field(ge=1.0, le=300.0, default=30.0)
    half_open_max_calls: int = Field(ge=1, le=100, default=5)
    window_size: int = Field(ge=10, le=1000, default=100)

class HealthCheckPolicy(BaseModel):
    """
    Health check configuration for service monitoring.
    
    Balances:
    - Detection speed (interval)
    - Resource usage (timeout)
    - False positive prevention (thresholds)
    
    WARNING: Short intervals may impact service performance
    """
    interval: float = Field(ge=1.0, le=300.0, default=30.0)
    timeout: float = Field(ge=0.1, le=30.0, default=5.0)
    unhealthy_threshold: int = Field(ge=1, le=10, default=3)
    healthy_threshold: int = Field(ge=1, le=10, default=2)

class ServiceConfig(BaseModel):
    """
    Service-specific configuration with policy defaults.
    
    Combines:
    - Basic service information
    - Load balancing preferences
    - Reliability policies
    - Health monitoring
    
    NOTE: Name validation ensures DNS compatibility
    """
    name: str
    host: str
    port: int = Field(ge=1, le=65535)
    tags: List[str] = Field(default_factory=list)
    load_balancing: LoadBalancingPolicy = LoadBalancingPolicy.ROUND_ROBIN
    retry_policy: RetryPolicy = RetryPolicy()
    circuit_breaker: CircuitBreakerPolicy = CircuitBreakerPolicy()
    health_check: HealthCheckPolicy = HealthCheckPolicy()
    
    @validator('name')
    def validate_name(cls, v):
        """
        Validate service name for mesh compatibility.
        
        Enforces:
        - Lowercase for case insensitivity
        - Alphanumeric for DNS compatibility
        - No special characters for shell safety
        """
        if not v.isalnum() or not v.islower():
            raise ValueError(
                'Service name must be lowercase alphanumeric'
            )
        return v

class MeshConfig(BaseModel):
    """
    Complete mesh configuration with global policies.
    
    Features:
    - Per-service configuration
    - Global policy defaults
    - Policy inheritance
    - Configuration validation
    
    TODO: Add configuration versioning
    """
    services: Dict[str, ServiceConfig]
    global_retry_policy: Optional[RetryPolicy] = None
    global_circuit_breaker: Optional[CircuitBreakerPolicy] = None
    global_health_check: Optional[HealthCheckPolicy] = None
    
    @validator('services')
    def validate_services(cls, v):
        if not v:
            raise ValueError('At least one service must be configured')
        return v
    
    def get_service_config(
        self,
        service_name: str,
        validate: bool = True
    ) -> ServiceConfig:
        """Get service configuration with validation"""
        if validate and service_name not in self.services:
            raise ValueError(f'Service {service_name} not configured')
        return self.services[service_name]
    
    def merge_with_globals(self, service_name: str) -> ServiceConfig:
        """
        Merge service config with global defaults.
        
        Process:
        1. Start with global policies
        2. Apply service-specific overrides
        3. Validate final configuration
        
        NOTE: Service settings take precedence over globals
        """
        service_config = self.get_service_config(service_name)
        
        if self.global_retry_policy:
            service_config.retry_policy = RetryPolicy(
                **{
                    **self.global_retry_policy.dict(),
                    **service_config.retry_policy.dict()
                }
            )
            
        if self.global_circuit_breaker:
            service_config.circuit_breaker = CircuitBreakerPolicy(
                **{
                    **self.global_circuit_breaker.dict(),
                    **service_config.circuit_breaker.dict()
                }
            )
            
        if self.global_health_check:
            service_config.health_check = HealthCheckPolicy(
                **{
                    **self.global_health_check.dict(),
                    **service_config.health_check.dict()
                }
            )
            
        return service_config 