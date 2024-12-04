import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from datapunk_shared.mesh import (
    MeshConfig,
    ConfigLoader,
    ConfigError,
    ConfigValidator
)

@pytest.fixture
def sample_config():
    return {
        "service": {
            "name": "test-service",
            "version": "1.0.0",
            "port": 8080
        },
        "discovery": {
            "hosts": ["discovery1:8500", "discovery2:8500"],
            "ttl": 30,
            "interval": 10
        },
        "security": {
            "tls_enabled": True,
            "cert_path": "/certs/service.crt",
            "key_path": "/certs/service.key"
        },
        "metrics": {
            "enabled": True,
            "port": 9090,
            "path": "/metrics"
        }
    }

@pytest.fixture
def config_loader():
    return ConfigLoader()

@pytest.mark.asyncio
async def test_config_loading(config_loader, sample_config):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_file.read.return_value = str(sample_config)
        mock_open.return_value.__aenter__.return_value = mock_file
        
        config = await config_loader.load("config.yaml")
        
        assert config["service"]["name"] == "test-service"
        assert config["service"]["port"] == 8080

@pytest.mark.asyncio
async def test_config_validation():
    validator = ConfigValidator()
    
    valid_config = {
        "service": {
            "name": "test-service",
            "port": 8080
        }
    }
    
    invalid_config = {
        "service": {
            "name": "test-service",
            "port": "invalid"  # Should be integer
        }
    }
    
    assert await validator.validate(valid_config)
    
    with pytest.raises(ConfigError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_config_hot_reload(config_loader):
    configs = []
    
    def config_handler(new_config):
        configs.append(new_config)
    
    config_loader.on_config_change(config_handler)
    
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_file.read.side_effect = [
            '{"version": "1.0.0"}',
            '{"version": "1.0.1"}',
            '{"version": "1.0.2"}'
        ]
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await config_loader.start_hot_reload("config.yaml", interval=0.1)
        await asyncio.sleep(0.3)
        await config_loader.stop_hot_reload()
        
        assert len(configs) >= 2
        assert configs[-1]["version"] == "1.0.2"

@pytest.mark.asyncio
async def test_config_inheritance():
    base_config = {
        "service": {
            "name": "base-service",
            "port": 8080
        },
        "logging": {
            "level": "INFO"
        }
    }
    
    override_config = {
        "service": {
            "name": "override-service"
        },
        "metrics": {
            "enabled": True
        }
    }
    
    loader = ConfigLoader()
    merged = await loader.merge_configs(base_config, override_config)
    
    assert merged["service"]["name"] == "override-service"
    assert merged["service"]["port"] == 8080
    assert merged["logging"]["level"] == "INFO"
    assert merged["metrics"]["enabled"] is True

@pytest.mark.asyncio
async def test_config_environment_variables():
    with patch.dict('os.environ', {
        'SERVICE_NAME': 'env-service',
        'SERVICE_PORT': '9090'
    }):
        loader = ConfigLoader()
        config = {
            "service": {
                "name": "${SERVICE_NAME}",
                "port": "${SERVICE_PORT}"
            }
        }
        
        resolved = await loader.resolve_variables(config)
        
        assert resolved["service"]["name"] == "env-service"
        assert resolved["service"]["port"] == "9090"

@pytest.mark.asyncio
async def test_config_file_watching():
    file_events = []
    
    def file_handler(event_type, file_path):
        file_events.append((event_type, file_path))
    
    loader = ConfigLoader()
    loader.on_file_change(file_handler)
    
    with patch('watchdog.observers.Observer'):
        await loader.watch_config_file("config.yaml")
        await asyncio.sleep(0.1)
        
        # Simulate file change event
        loader._handle_file_change("modified", "config.yaml")
        
        assert len(file_events) == 1
        assert file_events[0][0] == "modified"

@pytest.mark.asyncio
async def test_config_validation_rules():
    validator = ConfigValidator()
    
    # Add custom validation rule
    @validator.rule("service.port")
    def validate_port(value):
        return isinstance(value, int) and 1024 <= value <= 65535
    
    valid_config = {
        "service": {
            "port": 8080
        }
    }
    
    invalid_config = {
        "service": {
            "port": 80  # Below allowed range
        }
    }
    
    assert await validator.validate(valid_config)
    
    with pytest.raises(ConfigError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_config_schema_validation():
    schema = {
        "type": "object",
        "properties": {
            "service": {
                "type": "object",
                "required": ["name", "port"],
                "properties": {
                    "name": {"type": "string"},
                    "port": {"type": "integer"}
                }
            }
        }
    }
    
    validator = ConfigValidator(schema=schema)
    
    valid_config = {
        "service": {
            "name": "test-service",
            "port": 8080
        }
    }
    
    invalid_config = {
        "service": {
            "name": "test-service"
            # Missing required port
        }
    }
    
    assert await validator.validate(valid_config)
    
    with pytest.raises(ConfigError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_config_defaults():
    loader = ConfigLoader()
    
    defaults = {
        "service": {
            "port": 8080,
            "timeout": 30
        }
    }
    
    config = {
        "service": {
            "port": 9090
        }
    }
    
    merged = await loader.apply_defaults(config, defaults)
    
    assert merged["service"]["port"] == 9090  # Overridden value
    assert merged["service"]["timeout"] == 30  # Default value

@pytest.mark.asyncio
async def test_config_persistence(config_loader, sample_config):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Save config
        await config_loader.save_config("config.yaml", sample_config)
        mock_file.write.assert_called_once()
        
        # Load config
        mock_file.read.return_value = str(sample_config)
        loaded_config = await config_loader.load("config.yaml")
        
        assert loaded_config == sample_config

@pytest.mark.asyncio
async def test_config_encryption():
    with patch('cryptography.fernet.Fernet') as mock_fernet:
        mock_fernet.return_value.encrypt.return_value = b"encrypted"
        mock_fernet.return_value.decrypt.return_value = b'{"key": "value"}'
        
        loader = ConfigLoader()
        
        # Encrypt config
        config = {"key": "value"}
        encrypted = await loader.encrypt_config(config, "secret_key")
        assert encrypted == "encrypted"
        
        # Decrypt config
        decrypted = await loader.decrypt_config(encrypted, "secret_key")
        assert decrypted == {"key": "value"}

@pytest.mark.asyncio
async def test_config_validation_callbacks():
    validation_events = []
    
    def validation_handler(config, is_valid):
        validation_events.append((config, is_valid))
    
    validator = ConfigValidator()
    validator.on_validation(validation_handler)
    
    config = {
        "service": {
            "name": "test-service",
            "port": 8080
        }
    }
    
    await validator.validate(config)
    
    assert len(validation_events) == 1
    assert validation_events[0][1] is True  # is_valid

@pytest.mark.asyncio
async def test_cleanup(config_loader):
    cleanup_called = False
    
    async def cleanup_handler():
        nonlocal cleanup_called
        cleanup_called = True
    
    config_loader.on_cleanup(cleanup_handler)
    
    await config_loader.cleanup()
    
    assert cleanup_called 