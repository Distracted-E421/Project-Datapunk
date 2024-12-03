import pytest
from unittest.mock import Mock, patch
import os
import yaml
import json
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

from datapunk_shared.config.loader import ConfigLoader, ConfigurationError
from datapunk_shared.config.version_manager import ConfigVersionManager
from datapunk_shared.config.hot_reload import ConfigHotReloader

class TestConfig(BaseModel):
    """Sample config model for testing."""
    name: str
    port: int
    debug: bool = False
    api_key: Optional[str] = None

@pytest.fixture
def config_dir(tmp_path):
    """Create temporary config directory."""
    return tmp_path / "config"

@pytest.fixture
def sample_base_config():
    """Sample base configuration."""
    return {
        "name": "test-service",
        "port": 8080,
        "debug": False,
        "database": {
            "host": "localhost",
            "port": 5432
        }
    }

@pytest.fixture
def sample_env_config():
    """Sample environment-specific configuration."""
    return {
        "port": 9090,
        "debug": True,
        "database": {
            "host": "test-db",
            "username": "test_user"
        }
    }

@pytest.fixture
def config_loader(config_dir):
    """Create config loader instance."""
    return ConfigLoader(
        config_dir,
        env_prefix="TEST_",
        default_env="development"
    )

class TestConfigLoader:
    def test_initialization(self, config_dir):
        """Test config loader initialization."""
        loader = ConfigLoader(
            config_dir,
            env_prefix="TEST_",
            default_env="development",
            enable_hot_reload=True,
            enable_versioning=True
        )
        
        assert loader.config_dir == Path(config_dir)
        assert loader.env_prefix == "TEST_"
        assert loader.environment == "development"
        assert isinstance(loader.version_manager, ConfigVersionManager)
        assert isinstance(loader.hot_reloader, ConfigHotReloader)

    def test_environment_detection(self, config_dir):
        """Test environment detection from env vars."""
        with patch.dict(os.environ, {"TEST_ENV": "production"}):
            loader = ConfigLoader(config_dir, env_prefix="TEST_")
            assert loader.environment == "production"
        
        # Test default fallback
        loader = ConfigLoader(config_dir, env_prefix="TEST_", default_env="staging")
        assert loader.environment == "staging"

    def test_load_yaml_file(self, config_loader, config_dir, sample_base_config):
        """Test YAML file loading."""
        # Test existing file
        config_file = config_dir / "test.yml"
        config_dir.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            yaml.dump(sample_base_config, f)
        
        loaded = config_loader._load_yaml_file("test.yml")
        assert loaded == sample_base_config
        
        # Test non-existent file
        assert config_loader._load_yaml_file("nonexistent.yml") == {}
        
        # Test empty file
        empty_file = config_dir / "empty.yml"
        empty_file.touch()
        assert config_loader._load_yaml_file("empty.yml") == {}

    def test_deep_merge(self, config_loader, sample_base_config, sample_env_config):
        """Test deep dictionary merging."""
        merged = config_loader._deep_merge(sample_base_config, sample_env_config)
        
        # Check overridden values
        assert merged["port"] == sample_env_config["port"]
        assert merged["debug"] == sample_env_config["debug"]
        
        # Check merged nested dictionary
        assert merged["database"]["host"] == sample_env_config["database"]["host"]
        assert merged["database"]["port"] == sample_base_config["database"]["port"]
        assert merged["database"]["username"] == sample_env_config["database"]["username"]

    def test_env_var_overrides(self, config_loader, sample_base_config):
        """Test environment variable overrides."""
        env_vars = {
            "TEST_SERVICE_PORT": "5000",
            "TEST_SERVICE_DEBUG": "true",
            "TEST_SERVICE_DATABASE_HOST": "env-db",
            "TEST_SERVICE_NEW_SETTING": "value"
        }
        
        with patch.dict(os.environ, env_vars):
            config = config_loader._apply_env_overrides(
                sample_base_config,
                "TEST_SERVICE_"
            )
            
            assert config["port"] == 5000
            assert config["debug"] is True
            assert config["database"]["host"] == "env-db"
            assert config["new_setting"] == "value"

    def test_value_type_conversion(self, config_loader):
        """Test environment value type conversion."""
        # Test boolean conversion
        assert config_loader._convert_env_value("true") is True
        assert config_loader._convert_env_value("false") is False
        
        # Test numeric conversion
        assert config_loader._convert_env_value("123") == 123
        assert config_loader._convert_env_value("123.45") == 123.45
        
        # Test JSON conversion
        assert config_loader._convert_env_value('["a", "b"]') == ["a", "b"]
        assert config_loader._convert_env_value('{"key": "value"}') == {"key": "value"}
        
        # Test string fallback
        assert config_loader._convert_env_value("test") == "test"

    def test_load_config_with_model(self, config_loader, config_dir, sample_base_config):
        """Test configuration loading with Pydantic model validation."""
        # Create config files
        config_dir.mkdir(exist_ok=True)
        with open(config_dir / "service.yml", 'w') as f:
            yaml.dump(sample_base_config, f)
        
        # Load with model
        config = config_loader.load_config("service", TestConfig)
        assert isinstance(config, TestConfig)
        assert config.name == sample_base_config["name"]
        assert config.port == sample_base_config["port"]
        
        # Test invalid config
        invalid_config = {"name": "test"}  # Missing required field
        with open(config_dir / "invalid.yml", 'w') as f:
            yaml.dump(invalid_config, f)
        
        with pytest.raises(Exception):
            config_loader.load_config("invalid", TestConfig)

    @pytest.mark.asyncio
    async def test_hot_reload_integration(self, config_dir):
        """Test hot reload integration."""
        loader = ConfigLoader(
            config_dir,
            enable_hot_reload=True
        )
        
        # Initialize hot reload
        await loader.initialize()
        
        # Test callback registration
        callback = Mock()
        loader.register_callback("test", callback)
        
        # Verify callback was registered with hot reloader
        assert "test" in loader.hot_reloader.callbacks
        assert callback in loader.hot_reloader.callbacks["test"]

    def test_version_control_integration(self, config_dir, sample_base_config):
        """Test version control integration."""
        loader = ConfigLoader(
            config_dir,
            enable_versioning=True
        )
        
        # Create and load config
        config_dir.mkdir(exist_ok=True)
        with open(config_dir / "test.yml", 'w') as f:
            yaml.dump(sample_base_config, f)
        
        config = loader.load_config("test")
        
        # Verify version was created
        versions = loader.version_manager.get_version_history()
        assert len(versions) > 0
        assert versions[-1].changes == config

    def test_error_handling(self, config_loader):
        """Test error handling in config loading."""
        # Test invalid YAML
        with pytest.raises(Exception):
            config_loader._load_yaml_file("invalid.yml")
        
        # Test invalid environment variable type
        with patch.dict(os.environ, {"TEST_SERVICE_PORT": "invalid"}):
            with pytest.raises(ValueError):
                config_loader.load_config("service", TestConfig)
        
        # Test missing required config
        with pytest.raises(Exception):
            config_loader.load_config("nonexistent", TestConfig) 