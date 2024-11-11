from typing import Dict, Any, Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache
import yaml
import os

class CacheConfig(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    memory_cache_size: int = 1000
    default_ttl: int = 3600
    cache_levels: List[str] = ["memory", "redis"]
    warm_up: Dict[str, Any] = {
        "enabled": True,
        "interval": 300
    }

class ModelConfig(BaseSettings):
    name: str
    type: str
    version: str
    metrics: Dict[str, float]
    max_batch_size: int
    min_batch_size: Optional[int] = 1
    supports_streaming: bool
    resource_requirements: Optional[Dict[str, int]] = None

class Config(BaseSettings):
    cache: CacheConfig
    model_selection: Dict[str, List[ModelConfig]]
    integrations: Dict[str, Dict[str, Any]]

    @classmethod
    def load_from_yaml(cls, config_path: str) -> "Config":
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        # Replace environment variables
        config_data = cls._replace_env_vars(config_data)
        return cls(**config_data)

    @staticmethod
    def _replace_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively replace environment variables in config"""
        for key, value in config.items():
            if isinstance(value, dict):
                config[key] = Config._replace_env_vars(value)
            elif isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                if ':' in env_var:
                    env_var, default = env_var.split(':', 1)
                    config[key] = os.getenv(env_var, default)
                else:
                    config[key] = os.getenv(env_var)
        return config

@lru_cache()
def get_config(config_path: str = "config/settings.yaml") -> Config:
    return Config.load_from_yaml(config_path)

