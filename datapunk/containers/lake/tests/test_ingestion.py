import pytest
import asyncio
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Optional

from src.ingestion.core import (
    DataSource,
    ValidationLevel,
    ValidationResult,
    SchemaRegistry,
    ValidationEngine,
    DataIngestionManager
)
from src.ingestion.handlers import (
    RateLimitConfig,
    RateLimiter,
    ErrorContext,
    ErrorHandler,
    ExponentialBackoff,
    RetryHandler
)

# Test Models
class TestData(BaseModel):
    id: str
    value: int
    timestamp: datetime
    tags: Optional[List[str]] = None

# Test Fixtures
@pytest.fixture
def schema_registry():
    return SchemaRegistry()

@pytest.fixture
def validation_engine(schema_registry):
    return ValidationEngine(schema_registry, ValidationLevel.STRICT)

@pytest.fixture
def error_handler():
    handler = ErrorHandler()
    return handler

@pytest.fixture
def rate_limiter():
    config = RateLimitConfig(
        requests_per_second=10.0,
        burst_size=5,
        window_size=timedelta(seconds=1)
    )
    return RateLimiter(config)

# Schema Registry Tests
@pytest.mark.asyncio
async def test_schema_registration(schema_registry):
    await schema_registry.register_schema("test", TestData)
    schema = await schema_registry.get_schema("test")
    assert schema == TestData

@pytest.mark.asyncio
async def test_rule_registration(schema_registry):
    await schema_registry.register_schema("test", TestData)
    rules = [
        {"type": "required", "field": "id"},
        {"type": "range", "field": "value", "min": 0, "max": 100}
    ]
    await schema_registry.register_rules("test", rules)
    retrieved_rules = await schema_registry.get_rules("test")
    assert retrieved_rules == rules

# Validation Engine Tests
@pytest.mark.asyncio
async def test_validation_success(validation_engine, schema_registry):
    await schema_registry.register_schema("test", TestData)
    data = {
        "id": "test1",
        "value": 50,
        "timestamp": datetime.utcnow(),
        "tags": ["test"]
    }
    result = await validation_engine.validate(data, "test")
    assert result.is_valid
    assert not result.errors
    assert not result.warnings

@pytest.mark.asyncio
async def test_validation_failure(validation_engine, schema_registry):
    await schema_registry.register_schema("test", TestData)
    data = {
        "id": "test1",
        "value": "invalid",  # Should be int
        "timestamp": datetime.utcnow()
    }
    result = await validation_engine.validate(data, "test")
    assert not result.is_valid
    assert result.errors
    assert any("value" in str(error) for error in result.errors)

# Rate Limiter Tests
@pytest.mark.asyncio
async def test_rate_limiter_basic(rate_limiter):
    # Should allow burst size number of requests immediately
    results = []
    for _ in range(5):
        results.append(await rate_limiter.check_limit())
    assert all(results)

    # Should deny requests over burst size
    assert not await rate_limiter.check_limit()

@pytest.mark.asyncio
async def test_rate_limiter_recovery(rate_limiter):
    # Use up burst capacity
    for _ in range(5):
        await rate_limiter.check_limit()
    
    # Wait for token recovery
    await asyncio.sleep(1)
    
    # Should allow request after recovery
    assert await rate_limiter.check_limit()

# Error Handler Tests
@pytest.mark.asyncio
async def test_error_handler(error_handler):
    handled_errors = []
    
    async def test_handler(context: ErrorContext):
        handled_errors.append(context)
    
    await error_handler.register_handler("test_error", test_handler)
    await error_handler.start()
    
    context = ErrorContext(
        error_type="test_error",
        message="Test error message"
    )
    await error_handler.handle_error(context)
    
    # Wait for error processing
    await asyncio.sleep(0.1)
    
    assert len(handled_errors) == 1
    assert handled_errors[0].message == "Test error message"
    
    await error_handler.stop()

# Retry Handler Tests
@pytest.mark.asyncio
async def test_retry_handler():
    strategy = ExponentialBackoff(
        max_attempts=3,
        base_delay=0.1
    )
    handler = RetryHandler(strategy)
    
    attempt_count = 0
    
    async def failing_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError("Test error")
        return "success"
    
    result = await handler.execute_with_retry(failing_operation)
    assert result == "success"
    assert attempt_count == 3

@pytest.mark.asyncio
async def test_retry_handler_max_attempts():
    strategy = ExponentialBackoff(
        max_attempts=3,
        base_delay=0.1
    )
    handler = RetryHandler(strategy)
    
    async def always_failing_operation():
        raise ConnectionError("Test error")
    
    with pytest.raises(ConnectionError):
        await handler.execute_with_retry(always_failing_operation)

# Integration Tests
@pytest.mark.asyncio
async def test_full_ingestion_flow(schema_registry, validation_engine):
    # Setup
    await schema_registry.register_schema("test", TestData)
    manager = DataIngestionManager(validation_engine)
    
    class TestHandler:
        async def process(self, data):
            return data
    
    await manager.register_handler(DataSource.STRUCTURED, TestHandler())
    
    # Test valid data
    valid_data = {
        "id": "test1",
        "value": 50,
        "timestamp": datetime.utcnow(),
        "tags": ["test"]
    }
    result = await manager.ingest(valid_data, DataSource.STRUCTURED, "test")
    assert result.is_valid
    
    # Test invalid data
    invalid_data = {
        "id": "test2",
        "value": "invalid",
        "timestamp": datetime.utcnow()
    }
    result = await manager.ingest(invalid_data, DataSource.STRUCTURED, "test")
    assert not result.is_valid 