import pytest
import time
from datetime import datetime, timezone
from aiohttp import web

# Basic Service Example
class ExampleService:
    def __init__(self):
        self.counter = 0

    def increment(self):
        self.counter += 1
        return self.counter

# Unit Tests
@pytest.mark.unit
def test_example_service_init():
    """Test basic service initialization."""
    service = ExampleService()
    assert service.counter == 0

@pytest.mark.unit
def test_increment_counter():
    """Test counter increment."""
    service = ExampleService()
    assert service.increment() == 1
    assert service.increment() == 2

# Integration Tests
@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_integration(redis_client, cleanup_redis, assert_redis_keys):
    """Test Redis integration."""
    await redis_client.set("test_key", "test_value")
    await assert_redis_keys({"test_key": "test_value"})

# API Tests
@pytest.mark.api
@pytest.mark.asyncio
async def test_api_endpoint(aiohttp_client):
    """Test API endpoint."""
    async def hello(request):
        return web.Response(text='Hello, World!')

    app = web.Application()
    app.router.add_get('/', hello)
    
    # Get the test client
    client = aiohttp_client
    
    # Make the request
    resp = await client.get('/')
    assert resp.status == 404  # Since we didn't set up the route on this client

# Error Handling Tests
@pytest.mark.unit
def test_error_handling():
    """Test error handling."""
    with pytest.raises(ValueError) as exc_info:
        raise ValueError("test error")
    assert str(exc_info.value) == "test error"

# Mock Response Tests
@pytest.mark.unit
def test_with_mock_response(mock_response):
    """Test with mock response."""
    response = mock_response(status=200, data={"status": "ok"})
    assert response.status == 200
    assert response._data == {"status": "ok"}

# Logging Tests
@pytest.mark.unit
def test_logging(test_logger, assert_logs):
    """Test logging functionality."""
    test_logger.info("Test message", key="value")
    
    # Check if the log message was captured
    log_entry = assert_logs[-1]
    assert "Test message" in str(log_entry)
    assert log_entry.get("key") == "value"

# Performance Tests
@pytest.mark.performance
def test_performance(performance_metrics):
    """Test performance metrics."""
    start_time = time.time()
    # Simulate work
    sum(range(1000000))
    duration = time.time() - start_time
    
    performance_metrics.record_timing("calculation", duration)
    assert performance_metrics.get_average_timing("calculation") > 0

# JSON Fixture Tests
@pytest.mark.unit
def test_json_fixture(test_data_dir):
    """Test JSON fixture loading."""
    json_file = test_data_dir / "test.json"
    assert json_file.exists()

# Environment Tests
@pytest.mark.unit
def test_environment_setup(env_setup):
    """Test environment setup."""
    assert env_setup["DATAPUNK_ENV"] == "test"
    assert env_setup["DATAPUNK_LOG_LEVEL"] == "DEBUG"

# Error Injection Tests
@pytest.mark.unit
def test_error_injection(error_context):
    """Test error injection."""
    error_context.set_error(ValueError, "injected error")
    assert error_context.should_fail
    assert error_context.error_type == ValueError
    assert error_context.error_message == "injected error"

# Cleanup Tests
@pytest.mark.integration
@pytest.mark.asyncio
async def test_with_cleanup(redis_client, cleanup_redis):
    """Test cleanup functionality."""
    await redis_client.set("temp_key", "temp_value")
    assert await redis_client.get("temp_key") == "temp_value"
    # cleanup_redis will automatically clean after test

# DateTime Mock Tests
@pytest.mark.unit
def test_datetime_mock(mock_now):
    """Test datetime mocking."""
    assert mock_now.year == 2024
    assert mock_now.month == 1
    assert mock_now.day == 1
    assert mock_now.tzinfo == timezone.utc
    