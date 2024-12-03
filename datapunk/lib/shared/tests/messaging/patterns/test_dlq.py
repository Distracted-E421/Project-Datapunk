import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.messaging.patterns.dlq import DeadLetterQueue, DLQConfig
from datapunk_shared.monitoring import MetricsClient
from datapunk_shared.tracing import TracingManager

@pytest.fixture
def dlq_config():
    return DLQConfig(
        name="test_dlq",
        max_retries=3,
        retry_delay=5,
        expiration=3600,  # 1 hour
        max_size=1000,
        alert_threshold=0.8
    )

@pytest.fixture
def mock_metrics():
    return MagicMock(spec=MetricsClient)

@pytest.fixture
def mock_tracing():
    return MagicMock(spec=TracingManager)

@pytest.fixture
def mock_channel():
    channel = AsyncMock()
    exchange = AsyncMock()
    channel.default_exchange = exchange
    return channel

@pytest.fixture
def mock_connection():
    connection = AsyncMock()
    connection.channel.return_value = mock_channel()
    return connection

@pytest.fixture
async def dlq(dlq_config, mock_connection, mock_metrics, mock_tracing):
    dlq = DeadLetterQueue(mock_connection, dlq_config, mock_metrics, mock_tracing)
    await dlq.initialize()
    return dlq

@pytest.mark.asyncio
async def test_dlq_initialization(dlq, dlq_config, mock_connection):
    """Test DLQ initialization and setup"""
    channel = await mock_connection.channel()
    
    # Verify exchange declaration
    channel.declare_exchange.assert_called_with(
        f"{dlq_config.name}.dlx",
        durable=True
    )
    
    # Verify queue declaration
    channel.declare_queue.assert_called_with(
        dlq_config.name,
        durable=True,
        arguments={
            'x-max-length': dlq_config.max_size,
            'x-message-ttl': dlq_config.expiration * 1000,
            'x-dead-letter-exchange': f"{dlq_config.name}.dlx"
        }
    )

@pytest.mark.asyncio
async def test_message_routing(dlq, mock_connection):
    """Test message routing to DLQ"""
    message = {
        "id": "test-123",
        "payload": "test data",
        "error": "Processing failed"
    }
    
    await dlq.route_message(message)
    
    # Verify message was published to DLQ
    channel = await mock_connection.channel()
    channel.default_exchange.publish.assert_called_once()
    
    # Verify message properties
    published_message = channel.default_exchange.publish.call_args[0][0]
    assert published_message.headers['x-death-reason'] == "Processing failed"
    assert published_message.headers['x-original-id'] == "test-123"
    
    # Verify metrics
    dlq.metrics.increment.assert_called_with(
        'dlq_messages_total',
        {'queue': dlq.config.name}
    )

@pytest.mark.asyncio
async def test_message_reprocessing(dlq, mock_connection):
    """Test message reprocessing from DLQ"""
    # Setup mock message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.headers = {'retry_count': 1}
    message.message_id = "test-123"
    
    # Setup mock callback
    callback = AsyncMock()
    
    # Start reprocessing
    await dlq.reprocess_messages(callback)
    
    # Verify message processing
    queue = await dlq.channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    await handler(message)
    
    callback.assert_called_once_with('{"test": "data"}')
    dlq.metrics.increment.assert_called_with(
        'dlq_reprocessed_total',
        {'queue': dlq.config.name}
    )

@pytest.mark.asyncio
async def test_retry_exhaustion(dlq, mock_connection):
    """Test message handling when retries are exhausted"""
    message = {
        "id": "test-123",
        "payload": "test data",
        "retry_count": 3,
        "error": "Max retries reached"
    }
    
    await dlq.route_message(message)
    
    # Verify permanent failure handling
    dlq.metrics.increment.assert_any_call(
        'dlq_permanent_failures_total',
        {'queue': dlq.config.name}
    )

@pytest.mark.asyncio
async def test_size_monitoring(dlq, mock_connection):
    """Test DLQ size monitoring and alerts"""
    # Simulate queue size approaching threshold
    dlq.get_queue_size = AsyncMock(return_value=int(dlq.config.max_size * 0.9))
    
    await dlq.monitor_size()
    
    # Verify alert metrics
    dlq.metrics.gauge.assert_called_with(
        'dlq_size_ratio',
        0.9,
        {'queue': dlq.config.name}
    )
    dlq.metrics.increment.assert_called_with(
        'dlq_size_alerts_total',
        {'queue': dlq.config.name}
    )

@pytest.mark.asyncio
async def test_message_expiration(dlq, mock_connection):
    """Test message expiration handling"""
    # Setup expired message
    message = {
        "id": "test-123",
        "payload": "test data",
        "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()
    }
    
    await dlq.route_message(message)
    
    # Verify expiration metrics
    dlq.metrics.increment.assert_any_call(
        'dlq_expired_messages_total',
        {'queue': dlq.config.name}
    )

@pytest.mark.asyncio
async def test_error_tracking(dlq, mock_connection):
    """Test error tracking and categorization"""
    errors = [
        {"type": "ValidationError", "count": 5},
        {"type": "TimeoutError", "count": 3},
        {"type": "DatabaseError", "count": 2}
    ]
    
    for error in errors:
        message = {
            "id": f"test-{error['type']}",
            "payload": "test data",
            "error": error['type']
        }
        for _ in range(error['count']):
            await dlq.route_message(message)
    
    # Verify error tracking metrics
    for error in errors:
        dlq.metrics.increment.assert_any_call(
            'dlq_error_types_total',
            {'queue': dlq.config.name, 'error_type': error['type']},
            value=error['count']
        )

@pytest.mark.asyncio
async def test_cleanup(dlq, mock_connection):
    """Test DLQ cleanup operations"""
    # Setup mock messages
    expired_count = 5
    dlq.get_expired_messages = AsyncMock(return_value=[AsyncMock() for _ in range(expired_count)])
    
    await dlq.cleanup()
    
    # Verify cleanup metrics
    dlq.metrics.increment.assert_called_with(
        'dlq_cleaned_messages_total',
        {'queue': dlq.config.name},
        value=expired_count
    )

@pytest.mark.asyncio
async def test_tracing_integration(dlq, mock_connection):
    """Test tracing context integration"""
    message = {
        "id": "test-123",
        "payload": "test data",
        "error": "Test error"
    }
    
    await dlq.route_message(message)
    
    # Verify tracing attributes
    dlq.tracing.set_attribute.assert_any_call("dlq.message_id", "test-123")
    dlq.tracing.set_attribute.assert_any_call("dlq.error", "Test error")