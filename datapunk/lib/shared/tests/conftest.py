import os
import json
import pytest
import asyncio
from typing import AsyncGenerator, Generator, Any, Dict
import aiohttp
from aiohttp import web
import redis.asyncio as redis
import structlog
from datetime import datetime, timezone
from pathlib import Path

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

# Test Categories via Markers
def pytest_configure(config):
    """Configure custom markers to categorize tests."""
    markers = [
        "unit: Unit tests that test individual components in isolation",
        "integration: Tests that check multiple components working together",
        "api: Tests for API endpoints",
        "auth: Authentication and authorization tests",
        "security: Security-related tests",
        "performance: Tests that check performance metrics",
        "slow: Tests that take longer to run",
        "mesh: Service mesh related tests",
        "cache: Caching related tests",
        "database: Database related tests",
        "messaging: Messaging system tests",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)

# Utility Fixtures

@pytest.fixture
def test_data_dir() -> Path:
    """Provide path to test data directory."""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def load_json_fixture():
    """Helper to load JSON test data files."""
    def _load_json_fixture(filename: str) -> Dict[str, Any]:
        filepath = Path(__file__).parent / "test_data" / filename
        with open(filepath, "r") as f:
            return json.load(f)
    return _load_json_fixture

@pytest.fixture
def assert_logs():
    """Helper to assert log messages."""
    log_messages = []
    
    def _capture_log(event_dict):
        log_messages.append(event_dict)
        return event_dict
    
    old_processors = structlog.get_config()["processors"]
    structlog.configure(processors=[_capture_log] + old_processors)
    
    yield log_messages
    
    structlog.configure(processors=old_processors)

# Async Fixtures

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Mock Service Response Fixtures

@pytest.fixture
def mock_response():
    """Helper to create mock HTTP responses."""
    class MockResponse:
        def __init__(self, status: int = 200, data: Any = None, headers: Dict = None):
            self.status = status
            self._data = data
            self.headers = headers or {}

        async def json(self):
            return self._data

        async def text(self):
            return str(self._data)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockResponse

# Redis Fixtures

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

# HTTP Client Fixtures

@pytest.fixture
async def app():
    """Create base application for testing."""
    app = web.Application()
    return app

@pytest.fixture
async def aiohttp_client(aiohttp_client, app):
    """Create an aiohttp test client with the test application."""
    return await aiohttp_client(app)

# Time and Date Fixtures

@pytest.fixture
def mock_now():
    """Return a fixed datetime for time-dependent tests."""
    return datetime(2024, 1, 1, tzinfo=timezone.utc)

@pytest.fixture
def test_logger():
    """Create a structured logger for tests."""
    return structlog.get_logger()

# Environment Fixtures

@pytest.fixture(autouse=True)
def env_setup():
    """Set up environment variables for testing."""
    original_env = dict(os.environ)
    
    os.environ.update({
        "DATAPUNK_ENV": "test",
        "DATAPUNK_LOG_LEVEL": "DEBUG",
        "DATAPUNK_TEST_MODE": "true",
    })
    
    yield os.environ
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

# Test Helpers

@pytest.fixture
def assert_redis_keys(redis_client):
    """Helper to assert Redis key existence and values."""
    async def _assert_redis_keys(expected_keys: Dict[str, Any]):
        for key, expected_value in expected_keys.items():
            value = await redis_client.get(key)
            assert value == expected_value, f"Redis key {key} has value {value}, expected {expected_value}"
    return _assert_redis_keys

@pytest.fixture
def cleanup_redis(redis_client):
    """Clean up Redis after tests."""
    yield
    asyncio.get_event_loop().run_until_complete(redis_client.flushdb())

# Error Injection Fixtures

@pytest.fixture
def error_context():
    """Context for tracking injected errors in tests."""
    class ErrorContext:
        def __init__(self):
            self.should_fail = False
            self.error_type = None
            self.error_message = None

        def set_error(self, error_type, message):
            self.should_fail = True
            self.error_type = error_type
            self.error_message = message

        def clear_error(self):
            self.should_fail = False
            self.error_type = None
            self.error_message = None

    return ErrorContext()

# Performance Testing Fixtures

@pytest.fixture
def performance_metrics():
    """Helper for collecting performance metrics."""
    class PerformanceMetrics:
        def __init__(self):
            self.timings = {}
            self.counters = {}

        def record_timing(self, name: str, duration: float):
            if name not in self.timings:
                self.timings[name] = []
            self.timings[name].append(duration)

        def increment_counter(self, name: str, value: int = 1):
            self.counters[name] = self.counters.get(name, 0) + value

        def get_average_timing(self, name: str) -> float:
            timings = self.timings.get(name, [])
            return sum(timings) / len(timings) if timings else 0

        def get_counter(self, name: str) -> int:
            return self.counters.get(name, 0)

    return PerformanceMetrics()

# Database fixtures will be automatically handled by pytest-postgresql
# Redis fixtures will be automatically handled by pytest-redis

# Add more fixtures as needed for specific test cases 