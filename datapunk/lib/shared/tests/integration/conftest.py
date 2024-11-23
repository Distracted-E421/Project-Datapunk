import pytest
import asyncio
from typing import AsyncGenerator, Dict
import redis.asyncio as redis
import asyncpg
import aio_pika
from datapunk_shared.config import BaseServiceConfig
from datapunk_shared.metrics import MetricsCollector
from datapunk_shared.cache import CacheManager
from datapunk_shared.messaging import MessageQueue
from datapunk_shared.database import DatabaseManager

class IntegrationConfig(BaseServiceConfig):
    """Integration test configuration"""
    SERVICE_NAME: str = "integration-test"
    SERVICE_VERSION: str = "0.1.0"
    PORT: int = 8000
    
    # Service endpoints
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "test"
    DB_PASSWORD: str = "test"
    DB_NAME: str = "test_integration"
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = "guest"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def config():
    """Provide integration test configuration"""
    return IntegrationConfig()

@pytest.fixture(scope="session")
def metrics():
    """Provide metrics collector"""
    return MetricsCollector("integration-test")

@pytest.fixture(scope="session")
async def services(config, metrics) -> AsyncGenerator[Dict, None]:
    """Initialize and provide all services"""
    # Initialize services
    cache = CacheManager(config, metrics)
    await cache.initialize()
    
    db = DatabaseManager(config, metrics)
    await db.initialize()
    
    mq = MessageQueue(config, metrics)
    await mq.initialize()
    
    services = {
        "cache": cache,
        "db": db,
        "mq": mq
    }
    
    yield services
    
    # Cleanup
    await cache.redis.flushdb()
    await cache.redis.close()
    await db.pool.close()
    await mq.connection.close() 