import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
import aiohttp
from aiohttp import web
import redis.asyncio as redis
import structlog
from datetime import datetime, timezone

# Configure structured logging for tests
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.dict_tracebacks,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.BoundLogger,
    cache_logger_on_first_use=True,
)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Redis configuration
@pytest.fixture(scope="session")
def redis_proc(redis_proc_session):
    """Start Redis server."""
    return redis_proc_session

@pytest.fixture
async def redis_client(redis_proc) -> AsyncGenerator[redis.Redis, None]:
    """Create a Redis client connected to the test Redis server."""
    client = redis.Redis(
        host=redis_proc.host,
        port=redis_proc.port,
        decode_responses=True
    )
    try:
        await client.ping()
        yield client
    finally:
        await client.aclose()

@pytest.fixture
async def aiohttp_client(aiohttp_client):
    """Create an aiohttp test client."""
    app = web.Application()
    return await aiohttp_client(app)

@pytest.fixture
def mock_now():
    """Return a fixed datetime for time-dependent tests."""
    return datetime(2024, 1, 1, tzinfo=timezone.utc)

@pytest.fixture
def test_logger():
    """Create a structured logger for tests."""
    return structlog.get_logger()

# Environment setup
@pytest.fixture(autouse=True)
def env_setup():
    """Set up environment variables for testing."""
    os.environ["DATAPUNK_ENV"] = "test"
    os.environ["DATAPUNK_LOG_LEVEL"] = "DEBUG"
    return os.environ

# Database fixtures will be automatically handled by pytest-postgresql
# Redis fixtures will be automatically handled by pytest-redis

# Add more fixtures as needed for specific test cases 