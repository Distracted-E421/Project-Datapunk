from pydantic_settings import BaseSettings
from typing import Optional

class BaseServiceConfig(BaseSettings):
    """Base configuration for all services"""
    
    # Service Identity
    SERVICE_NAME: str
    SERVICE_VERSION: str = "1.0.0"
    
    # Network Settings
    HOST: str = "0.0.0.0"
    PORT: int
    
    # Consul Settings
    CONSUL_HOST: str = "consul"
    CONSUL_PORT: int = 8500
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Redis Settings
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True 