import pytest
from datetime import datetime, timezone

def test_environment(env_setup):
    """Verify test environment variables are set correctly."""
    assert env_setup["DATAPUNK_ENV"] == "test"
    assert env_setup["DATAPUNK_LOG_LEVEL"] == "DEBUG"

def test_mock_datetime(mock_now):
    """Verify mock datetime fixture works."""
    assert isinstance(mock_now, datetime)
    assert mock_now.tzinfo == timezone.utc

@pytest.mark.asyncio
async def test_redis_connection(redis_client):
    """Verify Redis connection works."""
    await redis_client.set("test_key", "test_value")
    value = await redis_client.get("test_key")
    assert value == "test_value"

@pytest.mark.asyncio
async def test_http_client(aiohttp_client):
    """Verify HTTP client fixture works."""
    client = await aiohttp_client
    assert client is not None 