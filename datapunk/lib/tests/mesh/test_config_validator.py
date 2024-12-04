import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datapunk_shared.mesh import (
    ConfigValidator,
    ValidationRule,
    ValidationError,
    ValidationResult
)

@pytest.fixture
def validator():
    return ConfigValidator()

@pytest.fixture
def sample_schema():
    return {
        "type": "object",
        "required": ["service", "security"],
        "properties": {
            "service": {
                "type": "object",
                "required": ["name", "port"],
                "properties": {
                    "name": {"type": "string"},
                    "port": {"type": "integer"},
                    "version": {"type": "string"}
                }
            },
            "security": {
                "type": "object",
                "properties": {
                    "tls_enabled": {"type": "boolean"},
                    "cert_path": {"type": "string"},
                    "key_path": {"type": "string"}
                }
            }
        }
    }

@pytest.mark.asyncio
async def test_basic_validation(validator):
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "integer"}
        }
    }
    
    validator.set_schema(schema)
    
    valid_config = {
        "name": "test",
        "value": 42
    }
    
    invalid_config = {
        "name": "test",
        "value": "not_an_integer"
    }
    
    assert await validator.validate(valid_config)
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_nested_validation(validator, sample_schema):
    validator.set_schema(sample_schema)
    
    valid_config = {
        "service": {
            "name": "test-service",
            "port": 8080,
            "version": "1.0.0"
        },
        "security": {
            "tls_enabled": True,
            "cert_path": "/certs/cert.pem",
            "key_path": "/certs/key.pem"
        }
    }
    
    invalid_config = {
        "service": {
            "name": "test-service",
            # Missing required port
            "version": "1.0.0"
        },
        "security": {
            "tls_enabled": True
        }
    }
    
    assert await validator.validate(valid_config)
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_custom_validation_rules(validator):
    # Add custom validation rules
    @validator.rule("service.port")
    def validate_port(value):
        return isinstance(value, int) and 1024 <= value <= 65535
    
    @validator.rule("service.name")
    def validate_name(value):
        return isinstance(value, str) and len(value) <= 50
    
    config = {
        "service": {
            "name": "test-service",
            "port": 8080
        }
    }
    
    invalid_config = {
        "service": {
            "name": "x" * 51,  # Too long
            "port": 80  # Below allowed range
        }
    }
    
    assert await validator.validate(config)
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_conditional_validation(validator):
    @validator.rule("security")
    def validate_security(value):
        if value.get("tls_enabled"):
            return all(key in value for key in ["cert_path", "key_path"])
        return True
    
    valid_configs = [
        {
            "security": {
                "tls_enabled": True,
                "cert_path": "/certs/cert.pem",
                "key_path": "/certs/key.pem"
            }
        },
        {
            "security": {
                "tls_enabled": False
            }
        }
    ]
    
    invalid_config = {
        "security": {
            "tls_enabled": True,
            # Missing cert_path and key_path
        }
    }
    
    for config in valid_configs:
        assert await validator.validate(config)
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_async_validation_rules(validator):
    @validator.async_rule("database")
    async def validate_database(value):
        await asyncio.sleep(0.1)  # Simulate async check
        return isinstance(value, dict) and "url" in value
    
    config = {
        "database": {
            "url": "postgresql://localhost:5432/db"
        }
    }
    
    invalid_config = {
        "database": {
            "host": "localhost"  # Missing url
        }
    }
    
    assert await validator.validate(config)
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_validation_context(validator):
    context = {"environment": "production"}
    
    @validator.rule("logging.level")
    def validate_log_level(value, ctx):
        if ctx["environment"] == "production":
            return value in ["WARNING", "ERROR"]
        return True
    
    config = {
        "logging": {
            "level": "DEBUG"
        }
    }
    
    # Should fail in production context
    with pytest.raises(ValidationError):
        await validator.validate(config, context=context)
    
    # Should pass in development context
    context["environment"] = "development"
    assert await validator.validate(config, context=context)

@pytest.mark.asyncio
async def test_validation_dependencies(validator):
    @validator.rule("cache.enabled")
    def validate_cache_enabled(value, config):
        if value and not config.get("redis", {}).get("url"):
            return False
        return True
    
    valid_config = {
        "cache": {
            "enabled": True
        },
        "redis": {
            "url": "redis://localhost:6379"
        }
    }
    
    invalid_config = {
        "cache": {
            "enabled": True
        }
        # Missing redis configuration
    }
    
    assert await validator.validate(valid_config)
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_validation_results(validator):
    results = []
    
    @validator.rule("service.name")
    def validate_name(value):
        if not value:
            results.append(ValidationResult(
                path="service.name",
                is_valid=False,
                message="Name cannot be empty"
            ))
            return False
        return True
    
    config = {
        "service": {
            "name": ""
        }
    }
    
    with pytest.raises(ValidationError):
        await validator.validate(config)
    
    assert len(results) == 1
    assert not results[0].is_valid
    assert "cannot be empty" in results[0].message

@pytest.mark.asyncio
async def test_schema_references(validator):
    schema = {
        "definitions": {
            "port": {
                "type": "integer",
                "minimum": 1024,
                "maximum": 65535
            }
        },
        "type": "object",
        "properties": {
            "http_port": {"$ref": "#/definitions/port"},
            "https_port": {"$ref": "#/definitions/port"}
        }
    }
    
    validator.set_schema(schema)
    
    valid_config = {
        "http_port": 8080,
        "https_port": 8443
    }
    
    invalid_config = {
        "http_port": 80,  # Below minimum
        "https_port": 8443
    }
    
    assert await validator.validate(valid_config)
    
    with pytest.raises(ValidationError):
        await validator.validate(invalid_config)

@pytest.mark.asyncio
async def test_validation_events(validator):
    events = []
    
    def validation_handler(event):
        events.append(event)
    
    validator.on_validation(validation_handler)
    
    config = {
        "name": "test"
    }
    
    await validator.validate(config)
    
    assert len(events) == 1
    assert events[0].config == config
    assert events[0].is_valid

@pytest.mark.asyncio
async def test_validation_metrics(validator):
    with patch('datapunk_shared.metrics.MetricsCollector') as mock_collector:
        config = {
            "name": "test"
        }
        
        await validator.validate(config)
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_validation_caching(validator):
    validation_count = 0
    
    @validator.rule("test")
    def validate_test(value):
        nonlocal validation_count
        validation_count += 1
        return True
    
    config = {
        "test": "value"
    }
    
    # First validation
    await validator.validate(config)
    assert validation_count == 1
    
    # Second validation with same config (should use cache)
    await validator.validate(config)
    assert validation_count == 1  # Should not increase

@pytest.mark.asyncio
async def test_cleanup(validator):
    cleanup_called = False
    
    async def cleanup_handler():
        nonlocal cleanup_called
        cleanup_called = True
    
    validator.on_cleanup(cleanup_handler)
    
    await validator.cleanup()
    
    assert cleanup_called 