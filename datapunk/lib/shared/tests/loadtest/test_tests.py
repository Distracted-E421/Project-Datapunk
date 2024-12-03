import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
from datapunk_shared.loadtest.tests import (
    APILoadTest,
    DatabaseLoadTest,
    CacheLoadTest,
    MessageQueueLoadTest
)

@pytest.fixture
def mock_session():
    with patch('aiohttp.ClientSession') as mock:
        session = Mock()
        session.request = AsyncMock()
        mock.return_value = session
        yield session

@pytest.fixture
def api_test():
    return APILoadTest(
        endpoint="http://test.api/endpoint",
        method="GET"
    )

@pytest.fixture
def db_test():
    return DatabaseLoadTest(
        query="SELECT * FROM test_table",
        connection_string="postgresql://test:test@localhost:5432/test_db"
    )

@pytest.fixture
def cache_test():
    return CacheLoadTest(
        host="localhost",
        port=6379,
        operation="GET",
        key_pattern="test:*"
    )

@pytest.fixture
def queue_test():
    return MessageQueueLoadTest(
        queue_name="test_queue",
        broker_url="amqp://guest:guest@localhost:5672/"
    )

@pytest.mark.asyncio
async def test_api_test_initialization(api_test):
    assert api_test.endpoint == "http://test.api/endpoint"
    assert api_test.method == "GET"
    assert api_test.name.startswith("API_GET")

@pytest.mark.asyncio
async def test_api_request_execution(api_test, mock_session):
    mock_session.request.return_value.__aenter__.return_value = Mock(
        status=200,
        elapsed_seconds=0.1
    )
    
    result = await api_test.execute_request()
    assert result is True
    mock_session.request.assert_called_once_with(
        "GET",
        "http://test.api/endpoint",
        json=None
    )

@pytest.mark.asyncio
async def test_api_error_handling(api_test, mock_session):
    # Test connection error
    mock_session.request.side_effect = aiohttp.ClientError()
    result = await api_test.execute_request()
    assert result is False
    
    # Test HTTP error
    mock_session.request.side_effect = None
    mock_session.request.return_value.__aenter__.return_value = Mock(
        status=500,
        elapsed_seconds=0.1
    )
    result = await api_test.execute_request()
    assert result is False

@pytest.mark.asyncio
async def test_database_test_execution(db_test):
    with patch('asyncpg.connect') as mock_connect:
        mock_conn = AsyncMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute = AsyncMock()
        
        result = await db_test.execute_request()
        assert result is True
        mock_conn.execute.assert_called_once_with(db_test.query)

@pytest.mark.asyncio
async def test_cache_test_execution(cache_test):
    with patch('aioredis.create_redis_pool') as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        
        result = await cache_test.execute_request()
        assert result is True
        
        if cache_test.operation == "GET":
            mock_client.get.assert_called_once()
        elif cache_test.operation == "SET":
            mock_client.set.assert_called_once()

@pytest.mark.asyncio
async def test_message_queue_test_execution(queue_test):
    with patch('aio_pika.connect_robust') as mock_connect:
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_connect.return_value = mock_connection
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        
        result = await queue_test.execute_request()
        assert result is True
        mock_channel.declare_queue.assert_called_once_with(queue_test.queue_name)

@pytest.mark.asyncio
async def test_api_payload_handling(api_test, mock_session):
    # Test with JSON payload
    api_test.payload = {"key": "value"}
    mock_session.request.return_value.__aenter__.return_value = Mock(
        status=200,
        elapsed_seconds=0.1
    )
    
    await api_test.execute_request()
    mock_session.request.assert_called_with(
        "GET",
        "http://test.api/endpoint",
        json={"key": "value"}
    )

@pytest.mark.asyncio
async def test_database_connection_pooling(db_test):
    with patch('asyncpg.create_pool') as mock_create_pool:
        mock_pool = AsyncMock()
        mock_create_pool.return_value = mock_pool
        
        # Test multiple requests using the same pool
        for _ in range(3):
            result = await db_test.execute_request()
            assert result is True
        
        # Pool should be created only once
        mock_create_pool.assert_called_once()

@pytest.mark.asyncio
async def test_cache_pattern_operations(cache_test):
    with patch('aioredis.create_redis_pool') as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        mock_client.keys = AsyncMock(return_value=["test:1", "test:2"])
        
        # Test pattern-based operations
        cache_test.operation = "SCAN"
        result = await cache_test.execute_request()
        assert result is True
        mock_client.keys.assert_called_once_with(cache_test.key_pattern)

@pytest.mark.asyncio
async def test_message_queue_publishing(queue_test):
    with patch('aio_pika.connect_robust') as mock_connect:
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_connect.return_value = mock_connection
        mock_connection.channel = AsyncMock(return_value=mock_channel)
        
        # Test message publishing
        queue_test.operation = "PUBLISH"
        queue_test.message = "test message"
        result = await queue_test.execute_request()
        assert result is True
        mock_channel.default_exchange.publish.assert_called_once() 