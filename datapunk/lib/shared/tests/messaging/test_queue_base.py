import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aio_pika
from datetime import datetime
from datapunk_shared.messaging.queue import MessageQueue, QueueConfig
from datapunk_shared.monitoring import MetricsClient
from datapunk_shared.tracing import TracingManager

@pytest.fixture
def queue_config():
    return QueueConfig(
        name="test_queue",
        durable=True,
        auto_delete=False,
        max_priority=10,
        max_length=1000,
        dead_letter_exchange="dlx",
        message_ttl=3600000,  # 1 hour
        max_retries=3
    )

@pytest.fixture
def mock_metrics():
    metrics = MagicMock(spec=MetricsClient)
    return metrics

@pytest.fixture
def mock_tracing():
    tracing = MagicMock(spec=TracingManager)
    return tracing

@pytest.fixture
def mock_channel():
    channel = AsyncMock()
    exchange = AsyncMock()
    channel.default_exchange = exchange
    return channel

@pytest.fixture
def mock_queue():
    queue = AsyncMock()
    queue.name = "test_queue"
    return queue

@pytest.fixture
def mock_connection():
    connection = AsyncMock()
    connection.channel.return_value = mock_channel()
    return connection

@pytest.fixture
async def message_queue(queue_config, mock_connection, mock_metrics, mock_tracing):
    queue = MessageQueue(mock_connection, queue_config, mock_metrics, mock_tracing)
    await queue.initialize()
    return queue

@pytest.mark.asyncio
async def test_queue_initialization(message_queue, queue_config, mock_connection):
    """Test queue initialization and setup"""
    channel = await mock_connection.channel()
    
    # Verify channel setup
    channel.set_qos.assert_called_once_with(prefetch_count=1)
    
    # Verify dead letter exchange declaration
    channel.declare_exchange.assert_called_once_with(
        "dlx",
        aio_pika.ExchangeType.DIRECT,
        durable=True
    )
    
    # Verify queue declaration
    channel.declare_queue.assert_called_once_with(
        queue_config.name,
        durable=True,
        auto_delete=False,
        arguments={
            'x-max-priority': 10,
            'x-max-length': 1000,
            'x-dead-letter-exchange': "dlx",
            'x-message-ttl': 3600000
        }
    )

@pytest.mark.asyncio
async def test_message_publishing(message_queue, mock_connection):
    """Test message publishing with monitoring"""
    message = {"key": "value"}
    correlation_id = "test-correlation-123"
    
    await message_queue.publish(message, priority=5, correlation_id=correlation_id)
    
    # Verify message was published
    channel = await mock_connection.channel()
    channel.default_exchange.publish.assert_called_once()
    
    # Verify message properties
    call_args = channel.default_exchange.publish.call_args[0]
    published_message = call_args[0]
    
    assert published_message.priority == 5
    assert published_message.correlation_id == correlation_id
    assert published_message.headers['retry_count'] == 0
    assert 'original_timestamp' in published_message.headers
    
    # Verify metrics
    message_queue.metrics.increment.assert_called_once_with(
        'messages_published_total',
        {'queue': 'test_queue'}
    )

@pytest.mark.asyncio
async def test_message_consumption(message_queue, mock_connection):
    """Test message consumption and processing"""
    # Create mock callback
    callback = AsyncMock()
    error_callback = AsyncMock()
    
    # Setup mock message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.headers = {'retry_count': 0}
    message.message_id = "test-123"
    
    # Start consumption
    await message_queue.consume(callback, error_callback)
    
    # Get message handler
    queue = await message_queue.channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process test message
    await handler(message)
    
    # Verify message processing
    message.process.assert_called_once()
    callback.assert_called_once_with('{"test": "data"}')
    message_queue.metrics.increment.assert_called_with(
        'messages_processed_total',
        {'queue': 'test_queue'}
    )

@pytest.mark.asyncio
async def test_message_retry(message_queue, mock_connection):
    """Test message retry handling"""
    callback = AsyncMock(side_effect=Exception("Processing failed"))
    error_callback = AsyncMock()
    
    # Setup mock message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.headers = {'retry_count': 0}
    message.message_id = "test-123"
    message.priority = 5
    message.correlation_id = "test-correlation"
    
    # Start consumption
    await message_queue.consume(callback, error_callback)
    
    # Get message handler
    queue = await message_queue.channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process test message
    with pytest.raises(Exception):
        await handler(message)
    
    # Verify retry attempt
    channel = await mock_connection.channel()
    channel.default_exchange.publish.assert_called_once()
    
    # Verify retry message properties
    retry_message = channel.default_exchange.publish.call_args[0][0]
    assert retry_message.headers['retry_count'] == 1
    assert retry_message.priority == 5
    assert retry_message.correlation_id == "test-correlation"
    assert retry_message.expiration > 0

@pytest.mark.asyncio
async def test_dead_letter_queue(message_queue, mock_connection):
    """Test dead letter queue routing after max retries"""
    callback = AsyncMock(side_effect=Exception("Processing failed"))
    error_callback = AsyncMock()
    
    # Setup mock message with max retries
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.headers = {'retry_count': 3}  # Max retries reached
    message.message_id = "test-123"
    
    # Start consumption
    await message_queue.consume(callback, error_callback)
    
    # Get message handler
    queue = await message_queue.channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process test message
    with pytest.raises(Exception):
        await handler(message)
    
    # Verify DLQ routing
    channel = await mock_connection.channel()
    dlq_publish = channel.default_exchange.publish.call_args[0][0]
    assert dlq_publish.headers.get('x-death', [])
    
    # Verify metrics
    message_queue.metrics.increment.assert_called_with(
        'message_processing_failures_total',
        {'queue': 'test_queue'}
    )

@pytest.mark.asyncio
async def test_priority_handling(message_queue, mock_connection):
    """Test message priority handling"""
    # Test with priority exceeding max
    await message_queue.publish({"test": "data"}, priority=15)
    
    channel = await mock_connection.channel()
    published_message = channel.default_exchange.publish.call_args[0][0]
    assert published_message.priority == 10  # Should be capped at max_priority

@pytest.mark.asyncio
async def test_error_callback(message_queue, mock_connection):
    """Test error callback execution"""
    callback = AsyncMock(side_effect=ValueError("Test error"))
    error_callback = AsyncMock()
    
    # Setup mock message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.headers = {'retry_count': 0}
    message.message_id = "test-123"
    
    # Start consumption
    await message_queue.consume(callback, error_callback)
    
    # Get message handler
    queue = await message_queue.channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process test message
    with pytest.raises(ValueError):
        await handler(message)
    
    # Verify error callback was called
    error_callback.assert_called_once()
    assert isinstance(error_callback.call_args[0][0], ValueError)

@pytest.mark.asyncio
async def test_tracing_integration(message_queue, mock_connection):
    """Test tracing context integration"""
    callback = AsyncMock()
    
    # Setup mock message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.headers = {'retry_count': 0}
    message.message_id = "test-123"
    
    # Start consumption
    await message_queue.consume(callback)
    
    # Get message handler
    queue = await message_queue.channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process test message
    await handler(message)
    
    # Verify tracing attributes were set
    message_queue.tracing.set_attribute.assert_any_call("message.id", "test-123")
    message_queue.tracing.set_attribute.assert_any_call("message.retry_count", 0) 