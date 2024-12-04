"""
Core Configuration Tests
-------------------

Tests the core configuration system including:
- Configuration loading
- Validation rules
- Environment integration
- Secret management
- Dynamic updates
- Security controls

Run with: pytest -v test_config.py
"""

import pytest
from datetime import timedelta
import os
import json
from unittest.mock import patch, mock_open

from datapunk_shared.auth.core.config import (
    AuthConfig,
    ConfigLoader,
    ConfigValidator,
    ConfigSource,
    SecretManager,
    EnvironmentConfig
)
from datapunk_shared.auth.core.exceptions import ConfigError

# Test Fixtures

@pytest.fixture
def secret_manager():
    """Mock secret manager for testing."""
    manager = Mock()
    manager.get_secret = Mock()
    manager.store_secret = Mock()
    return manager

@pytest.fixture
def config_validator():
    """Create config validator for testing."""
    return ConfigValidator()

@pytest.fixture
def config_loader(secret_manager, config_validator):
    """Create config loader for testing."""
    return ConfigLoader(
        secret_manager=secret_manager,
        validator=config_validator
    )

@pytest.fixture
def valid_config_data():
    """Create valid configuration data for testing."""
    return {
        "auth": {
            "session_ttl": 3600,
            "token_expiry": 86400,
            "max_sessions": 5,
            "require_mfa": True
        },
        "security": {
            "min_password_length": 12,
            "password_history": 5,
            "lockout_threshold": 3,
            "lockout_duration": 300
        },
        "rate_limiting": {
            "enabled": True,
            "max_requests": 1000,
            "window_size": 60
        }
    }

# Configuration Loading Tests

def test_config_loading(config_loader, valid_config_data):
    """Test configuration loading."""
    # Mock file reading
    with patch("builtins.open", mock_open(read_data=json.dumps(valid_config_data))):
        config = config_loader.load_config("config.json")
    
    assert config.auth.session_ttl == 3600
    assert config.auth.token_expiry == 86400
    assert config.auth.max_sessions == 5
    assert config.auth.require_mfa is True

def test_config_validation(config_loader):
    """Test configuration validation."""
    # Invalid session TTL
    invalid_data = {
        "auth": {
            "session_ttl": -1  # Invalid value
        }
    }
    
    with pytest.raises(ConfigError) as exc:
        config_loader.validate_config(invalid_data)
    assert "session_ttl" in str(exc.value)
    
    # Missing required field
    invalid_data = {
        "auth": {}  # Missing required fields
    }
    
    with pytest.raises(ConfigError) as exc:
        config_loader.validate_config(invalid_data)
    assert "required" in str(exc.value)

def test_environment_override(config_loader, valid_config_data):
    """Test environment variable override."""
    # Set environment variables
    with patch.dict(os.environ, {
        "AUTH_SESSION_TTL": "7200",
        "SECURITY_MIN_PASSWORD_LENGTH": "16"
    }):
        config = config_loader.load_config_with_env(valid_config_data)
    
    assert config.auth.session_ttl == 7200  # Overridden
    assert config.security.min_password_length == 16  # Overridden
    assert config.auth.max_sessions == 5  # Original value

# Secret Management Tests

def test_secret_loading(config_loader, secret_manager):
    """Test secret loading in configuration."""
    # Mock secret values
    secret_manager.get_secret.side_effect = {
        "db_password": "secret123",
        "api_key": "key123"
    }.get
    
    config_data = {
        "database": {
            "password": "${secret:db_password}"
        },
        "api": {
            "key": "${secret:api_key}"
        }
    }
    
    config = config_loader.load_config_with_secrets(config_data)
    
    assert config.database.password == "secret123"
    assert config.api.key == "key123"
    
    # Verify secret manager calls
    secret_manager.get_secret.assert_any_call("db_password")
    secret_manager.get_secret.assert_any_call("api_key")

def test_secret_validation(config_loader, secret_manager):
    """Test secret validation."""
    # Missing secret
    secret_manager.get_secret.return_value = None
    
    config_data = {
        "api": {
            "key": "${secret:missing_secret}"
        }
    }
    
    with pytest.raises(ConfigError) as exc:
        config_loader.load_config_with_secrets(config_data)
    assert "secret not found" in str(exc.value).lower()

# Dynamic Updates Tests

def test_config_updates(config_loader, valid_config_data):
    """Test dynamic configuration updates."""
    config = config_loader.load_config_with_env(valid_config_data)
    
    # Update single value
    config.update_value("auth.session_ttl", 7200)
    assert config.auth.session_ttl == 7200
    
    # Update multiple values
    config.update_values({
        "auth.max_sessions": 10,
        "security.min_password_length": 16
    })
    assert config.auth.max_sessions == 10
    assert config.security.min_password_length == 16

def test_update_validation(config_loader, valid_config_data):
    """Test validation during updates."""
    config = config_loader.load_config_with_env(valid_config_data)
    
    # Invalid value
    with pytest.raises(ConfigError) as exc:
        config.update_value("auth.session_ttl", -1)
    assert "invalid value" in str(exc.value).lower()
    
    # Invalid path
    with pytest.raises(ConfigError) as exc:
        config.update_value("invalid.path", "value")
    assert "path not found" in str(exc.value).lower()

# Environment Integration Tests

def test_environment_config():
    """Test environment configuration."""
    env_config = EnvironmentConfig()
    
    # Test environment detection
    assert env_config.is_production() is False
    assert env_config.is_development() is True
    
    # Test environment-specific settings
    dev_settings = env_config.get_environment_settings()
    assert dev_settings["debug"] is True
    assert dev_settings["logging_level"] == "DEBUG"

def test_environment_validation():
    """Test environment configuration validation."""
    # Invalid environment
    with pytest.raises(ConfigError) as exc:
        EnvironmentConfig(environment="invalid")
    assert "invalid environment" in str(exc.value).lower()
    
    # Missing required variables
    required_vars = ["DB_URL", "API_KEY"]
    with pytest.raises(ConfigError) as exc:
        EnvironmentConfig.validate_required_vars(required_vars)
    assert "missing required" in str(exc.value).lower()

# Security Tests

def test_sensitive_value_handling(config_loader):
    """Test handling of sensitive configuration values."""
    config_data = {
        "database": {
            "password": "sensitive_value",
            "api_key": "another_sensitive_value"
        }
    }
    
    # Sensitive values should be masked in string representation
    config = config_loader.load_config(config_data)
    config_str = str(config)
    
    assert "sensitive_value" not in config_str
    assert "another_sensitive_value" not in config_str
    assert "[REDACTED]" in config_str

def test_secure_loading(config_loader):
    """Test secure configuration loading."""
    # Test file permissions
    with pytest.raises(ConfigError) as exc:
        config_loader.load_config_secure("world_readable.json")
    assert "file permissions" in str(exc.value).lower()
    
    # Test secure parsing
    with pytest.raises(ConfigError) as exc:
        config_loader.load_config_secure('{"malicious": "__import__("os").system("rm -rf /")}')
    assert "security violation" in str(exc.value).lower()

# Performance Tests

def test_config_caching(config_loader, valid_config_data):
    """Test configuration caching."""
    # First load
    start_time = datetime.utcnow()
    config1 = config_loader.load_config(valid_config_data)
    first_load_time = (datetime.utcnow() - start_time).total_seconds()
    
    # Second load (should be cached)
    start_time = datetime.utcnow()
    config2 = config_loader.load_config(valid_config_data)
    second_load_time = (datetime.utcnow() - start_time).total_seconds()
    
    assert second_load_time < first_load_time
    assert config1 == config2

def test_bulk_operations(config_loader, valid_config_data):
    """Test bulk configuration operations."""
    # Bulk validation
    configs = [valid_config_data for _ in range(100)]
    
    start_time = datetime.utcnow()
    results = config_loader.validate_configs(configs)
    end_time = datetime.utcnow()
    
    assert len(results) == 100
    assert all(r.is_valid for r in results)
    assert (end_time - start_time).total_seconds() < 1.0  # Should be fast 