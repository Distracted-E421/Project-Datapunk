from typing import Dict, Any, Optional, Union, Type, Callable
import os
import yaml
import json
from pathlib import Path
from pydantic import BaseModel, ValidationError
import structlog
from ..utils.retry import RetryConfig
from .version_manager import ConfigVersionManager
from .hot_reload import ConfigHotReloader

logger = structlog.get_logger(__name__)

class ConfigLoader:
    """
    A configuration system that puts you in control
    
    Look, configuration doesn't need to be complicated. Load your configs, 
    override what you need, and get back to building something awesome. 
    This loader handles the heavy lifting while keeping things transparent 
    and maintainable.
    
    Features:
    - Environment-specific configs that just work
    - Hot reload when you need it
    - Version tracking that doesn't get in your way
    - Validation that catches problems early
    - Environment variables that override everything else
    
    Technical Notes:
    - YAML-based for readability
    - Nested config support
    - Smart type conversion
    - Pydantic model validation
    
    TODO: Add proper encryption for sensitive data
    FIXME: Improve validation error messages
    """
    
    def __init__(
        self,
        config_dir: Union[str, Path],
        env_prefix: str = "DATAPUNK_",
        default_env: str = "development",
        enable_hot_reload: bool = False,
        enable_versioning: bool = False
    ):
        """
        Set up your config loader exactly how you want it
        
        Args:
            config_dir: Root directory for your config files
            env_prefix: Prefix for env vars (defaults to DATAPUNK_)
            default_env: Fallback environment name
            enable_hot_reload: Watch for config changes in real-time
            enable_versioning: Keep track of config history
        
        The loader prioritizes like this:
        1. Environment variables (they win, always)
        2. Environment-specific config
        3. Base config
        
        Example:
            loader = ConfigLoader("./config", enable_hot_reload=True)
        """
        self.config_dir = Path(config_dir)
        self.env_prefix = env_prefix
        self.environment = os.getenv(f"{env_prefix}ENV", default_env)
        self.loaded_configs: Dict[str, Any] = {}
        
        # Initialize version manager if enabled
        self.version_manager = (
            ConfigVersionManager(str(self.config_dir / "versions"))
            if enable_versioning else None
        )
        
        # Initialize hot reloader if enabled
        self.hot_reloader = (
            ConfigHotReloader(
                str(self.config_dir),
                self.version_manager
            )
            if enable_hot_reload else None
        )
    
    async def initialize(self):
        """Initialize configuration system"""
        if self.hot_reloader:
            await self.hot_reloader.start()
    
    def register_callback(
        self,
        config_name: str,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """Register callback for configuration changes"""
        if self.hot_reloader:
            self.hot_reloader.register_callback(config_name, callback)
    
    def load_config(
        self,
        config_name: str,
        model: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        """Load configuration from files and environment variables"""
        try:
            # Base config
            base_config = self._load_yaml_file(f"{config_name}.yml")
            
            # Environment-specific config
            env_config = self._load_yaml_file(f"{config_name}.{self.environment}.yml")
            
            # Merge configurations
            merged_config = self._deep_merge(base_config, env_config)
            
            # Override with environment variables
            final_config = self._apply_env_overrides(
                merged_config,
                f"{self.env_prefix}{config_name.upper()}_"
            )
            
            # Validate against model if provided
            if model:
                final_config = model(**final_config)
                
            self.loaded_configs[config_name] = final_config
            return final_config
            
        except Exception as e:
            logger.error(
                "Failed to load configuration",
                config_name=config_name,
                error=str(e)
            )
            raise
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        file_path = self.config_dir / filename
        if not file_path.exists():
            return {}
            
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result:
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _apply_env_overrides(
        self,
        config: Dict[str, Any],
        prefix: str
    ) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        result = config.copy()
        
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue
                
            # Convert environment variable name to config key path
            config_path = env_key[len(prefix):].lower().split('_')
            
            # Apply the override
            current = result
            for part in config_path[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Convert value type based on existing config
            current[config_path[-1]] = self._convert_env_value(env_value)
            
        return result
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable value to appropriate type"""
        # Try to parse as JSON first
        try:
            return json.loads(value.lower())
        except json.JSONDecodeError:
            pass
        
        # Try to convert to int or float
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value

class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass 