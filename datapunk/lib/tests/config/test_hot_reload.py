import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
import yaml
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileModifiedEvent

from datapunk_shared.config.hot_reload import ConfigHotReloader, ConfigFileHandler
from datapunk_shared.config.version_manager import ConfigVersionManager

@pytest.fixture
def config_dir(tmp_path):
    """Create temporary config directory."""
    return tmp_path / "config"

@pytest.fixture
def version_manager(config_dir):
    """Create version manager instance."""
    version_dir = config_dir / "versions"
    return ConfigVersionManager(str(version_dir))

@pytest.fixture
def hot_reloader(config_dir, version_manager):
    """Create hot reloader instance."""
    return ConfigHotReloader(
        str(config_dir),
        version_manager=version_manager
    )

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "service": {
            "name": "test-service",
            "port": 8080
        },
        "logging": {
            "level": "info",
            "format": "json"
        }
    }

class TestConfigFileHandler:
    def test_initialization(self):
        """Test handler initialization."""
        callback = Mock()
        patterns = ["*.yml", "*.yaml", "*.json"]
        handler = ConfigFileHandler(callback, patterns)
        
        assert handler.callback == callback
        assert handler.patterns == patterns

    def test_file_modified_event(self):
        """Test handling of file modification events."""
        callback = Mock()
        handler = ConfigFileHandler(callback, ["*.yml"])
        
        # Test matching file
        event = FileModifiedEvent("test.yml")
        handler.on_modified(event)
        callback.assert_called_once_with("test.yml")
        
        # Test non-matching file
        callback.reset_mock()
        event = FileModifiedEvent("test.txt")
        handler.on_modified(event)
        callback.assert_not_called()
        
        # Test directory event
        callback.reset_mock()
        event = Mock(is_directory=True, src_path="test_dir")
        handler.on_modified(event)
        callback.assert_not_called()

class TestConfigHotReloader:
    @pytest.mark.asyncio
    async def test_initialization(self, hot_reloader, config_dir):
        """Test hot reloader initialization."""
        assert hot_reloader.config_dir == Path(config_dir)
        assert isinstance(hot_reloader.version_manager, ConfigVersionManager)
        assert hot_reloader.patterns == ["*.yml", "*.yaml", "*.json"]
        assert hot_reloader.callbacks == {}

    @pytest.mark.asyncio
    async def test_start_stop(self, hot_reloader):
        """Test starting and stopping the hot reloader."""
        with patch('watchdog.observers.Observer.start') as mock_start, \
             patch('watchdog.observers.Observer.stop') as mock_stop, \
             patch('watchdog.observers.Observer.join') as mock_join:
            
            # Test start
            await hot_reloader.start()
            mock_start.assert_called_once()
            
            # Test stop
            hot_reloader.stop()
            mock_stop.assert_called_once()
            mock_join.assert_called_once()

    def test_callback_registration(self, hot_reloader):
        """Test callback registration."""
        callback = Mock()
        config_type = "test_config"
        
        # Register callback
        hot_reloader.register_callback(config_type, callback)
        assert config_type in hot_reloader.callbacks
        assert callback in hot_reloader.callbacks[config_type]
        
        # Register another callback for same config
        callback2 = Mock()
        hot_reloader.register_callback(config_type, callback2)
        assert len(hot_reloader.callbacks[config_type]) == 2

    @pytest.mark.asyncio
    async def test_config_change_handling(self, hot_reloader, config_dir, sample_config):
        """Test handling of configuration changes."""
        config_file = config_dir / "test.yml"
        config_dir.mkdir(exist_ok=True)
        
        # Create initial config file
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        # Set up callback
        callback = Mock()
        hot_reloader.register_callback("test", callback)
        
        # Simulate file change
        await hot_reloader._handle_config_change(str(config_file))
        
        # Verify callback was called with config
        callback.assert_called_once()
        called_config = callback.call_args[0][0]
        assert called_config == sample_config

    @pytest.mark.asyncio
    async def test_version_control_integration(self, hot_reloader, config_dir, sample_config):
        """Test integration with version manager."""
        config_file = config_dir / "test.yml"
        config_dir.mkdir(exist_ok=True)
        
        # Create config file
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        # Handle config change
        await hot_reloader._handle_config_change(str(config_file))
        
        # Verify version was saved
        versions = hot_reloader.version_manager.get_version_history()
        assert len(versions) == 1
        assert versions[0].changes == sample_config

    @pytest.mark.asyncio
    async def test_error_handling(self, hot_reloader, config_dir):
        """Test error handling in config reload."""
        # Test invalid file
        with pytest.raises(Exception):
            await hot_reloader._handle_config_change("nonexistent.yml")
        
        # Test invalid YAML
        config_file = config_dir / "invalid.yml"
        config_dir.mkdir(exist_ok=True)
        config_file.write_text("invalid: yaml: content")
        
        with pytest.raises(Exception):
            await hot_reloader._handle_config_change(str(config_file))
        
        # Test callback error
        config_file = config_dir / "test.yml"
        with open(config_file, 'w') as f:
            yaml.dump({"test": "data"}, f)
        
        error_callback = Mock(side_effect=Exception("Callback failed"))
        hot_reloader.register_callback("test", error_callback)
        
        # Should not raise exception but log error
        await hot_reloader._handle_config_change(str(config_file))

    @pytest.mark.asyncio
    async def test_multiple_file_types(self, hot_reloader, config_dir, sample_config):
        """Test handling of different file types."""
        config_dir.mkdir(exist_ok=True)
        
        # Test YAML file
        yaml_file = config_dir / "test.yml"
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        # Test JSON file
        json_file = config_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump(sample_config, f)
        
        # Set up callbacks
        yaml_callback = Mock()
        json_callback = Mock()
        hot_reloader.register_callback("test", yaml_callback)
        hot_reloader.register_callback("test", json_callback)
        
        # Test both file types
        await hot_reloader._handle_config_change(str(yaml_file))
        await hot_reloader._handle_config_change(str(json_file))
        
        yaml_callback.assert_called_with(sample_config)
        json_callback.assert_called_with(sample_config) 