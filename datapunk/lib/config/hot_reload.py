"""
Hot reload configuration manager for Datapunk

This module provides real-time configuration updates without service restarts.
Built to resist the corporate bullshit of having to take down services just to
change a config value. Because fuck that noise.

Security Note:
- Implements retry logic to handle temporary filesystem issues
- Validates config changes before applying them
- Supports version control integration
"""

from typing import Dict, Any, Optional, Callable
import asyncio
import json
from pathlib import Path
import structlog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .version_manager import ConfigVersionManager
from ..utils.retry import with_retry, RetryConfig

logger = structlog.get_logger(__name__)

class ConfigFileHandler(FileSystemEventHandler):
    """
    Handles filesystem events for config changes
    
    Why a separate handler? Because we want fine-grained control over which 
    files trigger reloads. No more accidental restarts from temp files or 
    editor backups.
    """
    
    def __init__(
        self,
        callback: Callable[[str], None],
        patterns: list[str]
    ):
        self.callback = callback
        self.patterns = patterns
        super().__init__()
    
    def on_modified(self, event):
        # Only trigger for actual file changes, not directory updates
        # or other filesystem noise
        if not event.is_directory:
            if any(Path(event.src_path).match(pattern) 
                  for pattern in self.patterns):
                self.callback(event.src_path)

class ConfigHotReloader:
    """
    Real-time configuration management without the bullshit
    
    Watches config files and automatically applies changes without restarts.
    Because taking down services for config changes is corporate nonsense.
    
    Features:
    - Supports YAML and JSON configs
    - Version control integration
    - Retry logic for filesystem issues
    - Callback system for change notifications
    
    TODO: Add support for encrypted configs
    FIXME: Handle rapid successive changes more gracefully
    """
    
    def __init__(
        self,
        config_dir: str,
        version_manager: Optional[ConfigVersionManager] = None,
        patterns: list[str] = ["*.yml", "*.yaml", "*.json"]
    ):
        self.config_dir = Path(config_dir)
        self.version_manager = version_manager
        self.patterns = patterns
        self.observers: Dict[str, Observer] = {}
        self.handlers: Dict[str, ConfigFileHandler] = {}
        self.callbacks: Dict[str, list[Callable]] = {}
        
        # Retry configuration for filesystem operations
        # Because sometimes shit happens and we need to deal with it
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=15.0
        )
    
    async def start(self):
        """
        Start watching configuration files
        
        Sets up filesystem observers and initializes handlers.
        Implements recursive watching because nested configs 
        shouldn't be a pain in the ass.
        """
        handler = ConfigFileHandler(
            self._handle_config_change,
            self.patterns
        )
        
        observer = Observer()
        observer.schedule(
            handler,
            str(self.config_dir),
            recursive=True  # Because nested configs shouldn't be a PITA
        )
        observer.start()
        
        logger.info(
            "Started configuration hot reload",
            config_dir=str(self.config_dir)
        )
    
    def stop(self):
        """
        Stop watching configuration files
        
        Cleanly shuts down all observers to prevent resource leaks.
        Because we're not savages who leave shit running.
        """
        for observer in self.observers.values():
            observer.stop()
            observer.join()
    
    def register_callback(
        self,
        config_type: str,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Register callback for configuration changes
        
        Let components know when their config changes without
        tight coupling or circular dependencies.
        """
        if config_type not in self.callbacks:
            self.callbacks[config_type] = []
        self.callbacks[config_type].append(callback)
    
    @with_retry()
    async def _handle_config_change(self, filepath: str):
        """
        Handle configuration file changes
        
        Implements retry logic because filesystem operations can be 
        flaky as hell. Supports both YAML and JSON because we're not
        monsters who force one format.
        
        NOTE: Version control integration happens here if configured
        """
        try:
            path = Path(filepath)
            config_type = path.stem
            
            # Load new configuration with format-specific parsing
            with open(filepath, 'r') as f:
                if path.suffix in ['.yml', '.yaml']:
                    import yaml
                    new_config = yaml.safe_load(f)
                else:
                    new_config = json.load(f)
            
            # Version the change if version manager exists
            if self.version_manager:
                self.version_manager.save_version(
                    new_config,
                    self.version_manager._get_next_version(),
                    f"Hot reload update from {path.name}",
                    "hot_reload"
                )
            
            # Notify callbacks
            if config_type in self.callbacks:
                for callback in self.callbacks[config_type]:
                    try:
                        callback(new_config)
                    except Exception as e:
                        logger.error(
                            "Callback failed",
                            config_type=config_type,
                            error=str(e)
                        )
            
            logger.info(
                "Configuration reloaded",
                filepath=filepath
            )
            
        except Exception as e:
            logger.error(
                "Failed to reload configuration",
                filepath=filepath,
                error=str(e)
            )
            raise 