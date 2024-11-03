import yaml
from typing import Dict, Any
import os

def load_config(config_path: str) -> Dict[str, Any]:
    """Load and parse YAML configuration file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Replace environment variables
    _replace_env_vars(config)
    return config

def _replace_env_vars(config: Dict[str, Any]):
    """Recursively replace environment variables in config"""
    for key, value in config.items():
        if isinstance(value, dict):
            _replace_env_vars(value)
        elif isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_var = value[2:-1]
            config[key] = os.getenv(env_var)
