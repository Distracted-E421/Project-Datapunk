from typing import Any, Dict, Optional
import os
import yaml
from dataclasses import dataclass
from .exceptions import ConfigError, MissingConfigError, InvalidConfigError

@dataclass
class ServiceConfig:
    """Base service configuration for Datapunk microservices.
    
    Defines core service parameters required for operation within the mesh.
    NOTE: All services must provide name, version, and environment.
    """
    name: str
    version: str
    environment: str
    log_level: str = "INFO"
    metrics_enabled: bool = True
    tracing_enabled: bool = True

@dataclass
class MeshConfig:
    """Service mesh configuration for inter-service communication.
    
    Handles service discovery and communication patterns within the mesh.
    NOTE: Consul is the primary service discovery mechanism
    TODO: Add support for alternative service discovery providers
    """
    consul_host: str
    consul_port: int
    enable_mtls: bool = True
    enable_metrics: bool = True
    load_balancer_strategy: str = "round_robin"
    circuit_breaker_enabled: bool = True
    retry_enabled: bool = True

@dataclass
class CacheConfig:
    """Redis cache configuration for distributed caching.
    
    Manages caching behavior and connection settings.
    NOTE: Default TTL of 1 hour can be overridden per service
    """
    redis_host: str
    redis_port: int
    ttl: int = 3600  # Default 1 hour TTL
    max_connections: int = 10
    enable_cluster: bool = False

class ConfigLoader:
    """Configuration loader with environment variable override support.
    
    Loads configuration from YAML files and allows override through environment
    variables using the DP_ prefix. Supports nested configuration using
    dot notation in both YAML and environment variables.
    
    Example:
        YAML: service.name: "auth"
        Env: DP_SERVICE_NAME="auth"
    
    NOTE: Environment variables take precedence over file configuration
    FIXME: Add support for configuration reloading without service restart
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration loader.
        
        Args:
            config_path: Path to YAML configuration file
                        Falls back to CONFIG_PATH environment variable
        """
        self.config_path = config_path or os.getenv("CONFIG_PATH")
        self.config_data: Dict[str, Any] = {}
        
    def load(self) -> Dict[str, Any]:
        """Load and validate configuration from file and environment.
        
        Returns:
            Merged configuration dictionary
            
        Raises:
            InvalidConfigError: If YAML parsing fails
            MissingConfigError: If required values are missing
            ConfigError: For other configuration-related errors
        """
        try:
            # Load from file if exists
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path) as f:
                    self.config_data = yaml.safe_load(f)
            
            # Environment variables override file configuration
            self._override_from_env()
            
            # Ensure all required values are present
            self._validate_config()
            
            return self.config_data
            
        except yaml.YAMLError as e:
            raise InvalidConfigError(f"Invalid YAML configuration: {str(e)}")
        except Exception as e:
            raise ConfigError(f"Configuration loading failed: {str(e)}")
    
    def _override_from_env(self):
        """Override configuration with environment variables.
        
        Environment variables prefixed with DP_ are mapped to nested
        configuration keys using underscore separation.
        Example: DP_SERVICE_NAME -> service.name
        """
        for key, value in os.environ.items():
            if key.startswith("DP_"):  # Datapunk prefix
                config_key = key[3:].lower()
                self._set_nested_value(self.config_data, config_key.split('_'), value)
    
    def _set_nested_value(self, data: Dict, keys: list, value: Any):
        """Set value in nested dictionary using key path.
        
        Args:
            data: Target dictionary
            keys: List of nested keys
            value: Value to set
        """
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value
    
    def _validate_config(self):
        """Validate required configuration values.
        
        Ensures critical configuration values are present.
        TODO: Add type validation for configuration values
        """
        required_keys = [
            "service.name",
            "service.version",
            "service.environment"
        ]
        
        for key in required_keys:
            if not self._get_nested_value(self.config_data, key.split('.')):
                raise MissingConfigError(f"Missing required configuration: {key}")
    
    def _get_nested_value(self, data: Dict, keys: list) -> Any:
        """Get value from nested dictionary using key path.
        
        Args:
            data: Source dictionary
            keys: List of nested keys
        
        Returns:
            Value if found, None otherwise
        """
        for key in keys:
            if not isinstance(data, dict) or key not in data:
                return None
            data = data[key]
        return data

    def get_service_config(self) -> ServiceConfig:
        """Get service configuration as dataclass.
        
        Returns:
            ServiceConfig with current configuration values
        """
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
        """Get mesh configuration as dataclass.
        
        Returns:
            MeshConfig with current configuration values
        """
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
        """Get cache configuration as dataclass.
        
        Returns:
            CacheConfig with current configuration values
        """
        cache = self.config_data.get("cache", {})
        return CacheConfig(
            redis_host=cache.get("redis_host", "redis"),
            redis_port=cache.get("redis_port", 6379),
            ttl=cache.get("ttl", 3600),
            max_connections=cache.get("max_connections", 10),
            enable_cluster=cache.get("enable_cluster", False)
        ) 