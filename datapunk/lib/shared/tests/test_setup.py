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
async def test_http_client(aiohttp_client):
    """Verify HTTP client fixture works."""
    client = await aiohttp_client
    assert client is not None

def test_logger(test_logger):
    """Verify logger fixture works."""
    test_logger.info("Test log message")
    assert True  # If we get here, logging didn't raise any exceptions 