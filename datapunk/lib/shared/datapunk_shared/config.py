from typing import Any, Dict, Optional
import os
import yaml
from dataclasses import dataclass
from .exceptions import ConfigError, MissingConfigError, InvalidConfigError

@dataclass
class ServiceConfig:
    """Base service configuration."""
    name: str
    version: str
    environment: str
    log_level: str = "INFO"
    metrics_enabled: bool = True
    tracing_enabled: bool = True

@dataclass
class MeshConfig:
    """Service mesh configuration."""
    consul_host: str
    consul_port: int
    enable_mtls: bool = True
    enable_metrics: bool = True
    load_balancer_strategy: str = "round_robin"
    circuit_breaker_enabled: bool = True
    retry_enabled: bool = True

@dataclass
class CacheConfig:
    """Cache configuration."""
    redis_host: str
    redis_port: int
    ttl: int = 3600
    max_connections: int = 10
    enable_cluster: bool = False

class ConfigLoader:
    """Configuration loader with environment variable support."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv("CONFIG_PATH")
        self.config_data: Dict[str, Any] = {}
        
    def load(self) -> Dict[str, Any]:
        """Load configuration from file and environment."""
        try:
            # Load from file if exists
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path) as f:
                    self.config_data = yaml.safe_load(f)
            
            # Override with environment variables
            self._override_from_env()
            
            # Validate configuration
            self._validate_config()
            
            return self.config_data
            
        except yaml.YAMLError as e:
            raise InvalidConfigError(f"Invalid YAML configuration: {str(e)}")
        except Exception as e:
            raise ConfigError(f"Configuration loading failed: {str(e)}")
    
    def _override_from_env(self):
        """Override configuration with environment variables."""
        for key, value in os.environ.items():
            if key.startswith("DP_"):  # Datapunk prefix
                config_key = key[3:].lower()
                self._set_nested_value(self.config_data, config_key.split('_'), value)
    
    def _set_nested_value(self, data: Dict, keys: list, value: Any):
        """Set value in nested dictionary."""
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value
    
    def _validate_config(self):
        """Validate required configuration values."""
        required_keys = [
            "service.name",
            "service.version",
            "service.environment"
        ]
        
        for key in required_keys:
            if not self._get_nested_value(self.config_data, key.split('.')):
                raise MissingConfigError(f"Missing required configuration: {key}")
    
    def _get_nested_value(self, data: Dict, keys: list) -> Any:
        """Get value from nested dictionary."""
        for key in keys:
            if not isinstance(data, dict) or key not in data:
                return None
            data = data[key]
        return data

    def get_service_config(self) -> ServiceConfig:
        """Get service configuration."""
        service = self.config_data.get("service", {})
        return ServiceConfig(
            name=service["name"],
            version=service["version"],
            environment=service["environment"],
            log_level=service.get("log_level", "INFO"),
            metrics_enabled=service.get("metrics_enabled", True),
            tracing_enabled=service.get("tracing_enabled", True)
        )

    def get_mesh_config(self) -> MeshConfig:
        """Get mesh configuration."""
        mesh = self.config_data.get("mesh", {})
        return MeshConfig(
            consul_host=mesh.get("consul_host", "consul"),
            consul_port=mesh.get("consul_port", 8500),
            enable_mtls=mesh.get("enable_mtls", True),
            enable_metrics=mesh.get("enable_metrics", True),
            load_balancer_strategy=mesh.get("load_balancer_strategy", "round_robin"),
            circuit_breaker_enabled=mesh.get("circuit_breaker_enabled", True),
            retry_enabled=mesh.get("retry_enabled", True)
        )

    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration."""
        cache = self.config_data.get("cache", {})
        return CacheConfig(
            redis_host=cache.get("redis_host", "redis"),
            redis_port=cache.get("redis_port", 6379),
            ttl=cache.get("ttl", 3600),
            max_connections=cache.get("max_connections", 10),
            enable_cluster=cache.get("enable_cluster", False)
        ) 