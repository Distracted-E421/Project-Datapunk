import pytest
import asyncio
from typing import AsyncGenerator
import redis.asyncio as redis
import asyncpg
import aio_pika
from datapunk_shared.config import BaseServiceConfig
from datapunk_shared.metrics import MetricsCollector

class TestConfig(BaseServiceConfig):
    """Test configuration"""
    SERVICE_NAME: str = "test-service"
    SERVICE_VERSION: str = "0.1.0"
    PORT: int = 8000
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "test"
    DB_PASSWORD: str = "test"
    DB_NAME: str = "test"
    
    # RabbitMQ settings
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = "guest"

@pytest.fixture
def config():
    """Provide test configuration"""
    return TestConfig()

@pytest.fixture
def metrics():
    """Provide metrics collector"""
    return MetricsCollector("test-service")

@pytest.fixture
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """Provide Redis client"""
    client = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
        db=1  # Use separate DB for tests
    )
    yield client
    await client.flushdb()  # Clean up after tests
    await client.close()

@pytest.fixture
async def pg_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """Provide PostgreSQL connection pool"""
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        user="test",
        password="test",
        database="test"
    )
    yield pool
    await pool.close()

@pytest.fixture
async def rabbitmq_connection() -> AsyncGenerator[aio_pika.Connection, None]:
    """Provide RabbitMQ connection"""
    connection = await aio_pika.connect_robust(
        host="localhost",
        port=5672,
        login="guest",
        password="guest"
    )
    yield connection
    await connection.close() 