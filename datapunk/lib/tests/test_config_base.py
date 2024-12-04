import pytest
import os
import yaml
from unittest.mock import mock_open, patch
from datapunk_shared.config import (
    ServiceConfig, MeshConfig, CacheConfig, ConfigLoader,
    ConfigError, MissingConfigError, InvalidConfigError
)

@pytest.fixture
def valid_config_data():
    return {
        "service": {
            "name": "test-service",
            "version": "1.0.0",
            "environment": "test",
            "log_level": "DEBUG",
            "metrics_enabled": True,
            "tracing_enabled": True
        },
        "mesh": {
            "consul_host": "localhost",
            "consul_port": 8500,
            "enable_mtls": True,
            "enable_metrics": True,
            "load_balancer_strategy": "round_robin",
            "circuit_breaker_enabled": True,
            "retry_enabled": True
        },
        "cache": {
            "redis_host": "localhost",
            "redis_port": 6379,
            "ttl": 3600,
            "max_connections": 10,
            "enable_cluster": False
        }
    }

@pytest.fixture
def config_yaml(valid_config_data):
    return yaml.dump(valid_config_data)

@pytest.fixture
def config_loader():
    return ConfigLoader("test_config.yaml")

def test_service_config_dataclass():
    """Test ServiceConfig dataclass initialization and defaults"""
    config = ServiceConfig(
        name="test",
        version="1.0.0",
        environment="dev"
    )
    assert config.name == "test"
    assert config.version == "1.0.0"
    assert config.environment == "dev"
    assert config.log_level == "INFO"  # default value
    assert config.metrics_enabled is True  # default value
    assert config.tracing_enabled is True  # default value

def test_mesh_config_dataclass():
    """Test MeshConfig dataclass initialization and defaults"""
    config = MeshConfig(
        consul_host="localhost",
        consul_port=8500
    )
    assert config.consul_host == "localhost"
    assert config.consul_port == 8500
    assert config.enable_mtls is True  # default value
    assert config.load_balancer_strategy == "round_robin"  # default value
    assert config.circuit_breaker_enabled is True  # default value
    assert config.retry_enabled is True  # default value

def test_cache_config_dataclass():
    """Test CacheConfig dataclass initialization and defaults"""
    config = CacheConfig(
        redis_host="localhost",
        redis_port=6379
    )
    assert config.redis_host == "localhost"
    assert config.redis_port == 6379
    assert config.ttl == 3600  # default value
    assert config.max_connections == 10  # default value
    assert config.enable_cluster is False  # default value

def test_config_loader_file_loading(config_yaml):
    """Test loading configuration from YAML file"""
    with patch("builtins.open", mock_open(read_data=config_yaml)):
        loader = ConfigLoader("test_config.yaml")
        config = loader.load()
        
        assert config["service"]["name"] == "test-service"
        assert config["mesh"]["consul_host"] == "localhost"
        assert config["cache"]["redis_port"] == 6379

def test_config_loader_env_override(config_yaml):
    """Test environment variable override of configuration"""
    with patch("builtins.open", mock_open(read_data=config_yaml)):
        with patch.dict(os.environ, {
            "DP_SERVICE_NAME": "override-service",
            "DP_MESH_CONSUL_PORT": "9500",
            "DP_CACHE_TTL": "7200"
        }):
            loader = ConfigLoader("test_config.yaml")
            config = loader.load()
            
            assert config["service"]["name"] == "override-service"
            assert config["mesh"]["consul_port"] == "9500"
            assert config["cache"]["ttl"] == "7200"

def test_config_loader_missing_required():
    """Test handling of missing required configuration"""
    invalid_config = {
        "service": {
            "name": "test-service",
            # missing version and environment
        }
    }
    
    with patch("builtins.open", mock_open(read_data=yaml.dump(invalid_config))):
        loader = ConfigLoader("test_config.yaml")
        with pytest.raises(MissingConfigError) as exc_info:
            loader.load()
        assert "Missing required configuration" in str(exc_info.value)

def test_config_loader_invalid_yaml():
    """Test handling of invalid YAML configuration"""
    with patch("builtins.open", mock_open(read_data="invalid: yaml: content:")):
        loader = ConfigLoader("test_config.yaml")
        with pytest.raises(InvalidConfigError) as exc_info:
            loader.load()
        assert "Invalid YAML configuration" in str(exc_info.value)

def test_get_service_config(config_loader, valid_config_data):
    """Test getting ServiceConfig dataclass from loaded configuration"""
    config_loader.config_data = valid_config_data
    service_config = config_loader.get_service_config()
    
    assert isinstance(service_config, ServiceConfig)
    assert service_config.name == "test-service"
    assert service_config.version == "1.0.0"
    assert service_config.environment == "test"
    assert service_config.log_level == "DEBUG"

def test_get_mesh_config(config_loader, valid_config_data):
    """Test getting MeshConfig dataclass from loaded configuration"""
    config_loader.config_data = valid_config_data
    mesh_config = config_loader.get_mesh_config()
    
    assert isinstance(mesh_config, MeshConfig)
    assert mesh_config.consul_host == "localhost"
    assert mesh_config.consul_port == 8500
    assert mesh_config.enable_mtls is True
    assert mesh_config.load_balancer_strategy == "round_robin"

def test_get_cache_config(config_loader, valid_config_data):
    """Test getting CacheConfig dataclass from loaded configuration"""
    config_loader.config_data = valid_config_data
    cache_config = config_loader.get_cache_config()
    
    assert isinstance(cache_config, CacheConfig)
    assert cache_config.redis_host == "localhost"
    assert cache_config.redis_port == 6379
    assert cache_config.ttl == 3600
    assert cache_config.max_connections == 10
    assert cache_config.enable_cluster is False

def test_nested_value_handling(config_loader):
    """Test handling of nested configuration values"""
    test_data = {"a": {"b": {"c": "value"}}}
    
    # Test setting nested value
    config_loader._set_nested_value(test_data, ["x", "y", "z"], "new_value")
    assert test_data["x"]["y"]["z"] == "new_value"
    
    # Test getting nested value
    assert config_loader._get_nested_value(test_data, ["a", "b", "c"]) == "value"
    assert config_loader._get_nested_value(test_data, ["a", "b", "missing"]) is None
    assert config_loader._get_nested_value(test_data, ["missing"]) is None

def test_config_path_from_env():
    """Test loading config path from environment variable"""
    with patch.dict(os.environ, {"CONFIG_PATH": "/path/to/config.yaml"}):
        loader = ConfigLoader()
        assert loader.config_path == "/path/to/config.yaml"

def test_empty_config_handling():
    """Test handling of empty configuration"""
    with patch("builtins.open", mock_open(read_data="")):
        loader = ConfigLoader("test_config.yaml")
        with pytest.raises(MissingConfigError):
            loader.load() 