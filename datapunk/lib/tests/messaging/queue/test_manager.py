import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.messaging.queue.manager import QueueManager, QueueManagerConfig
from datapunk_shared.monitoring import MetricsClient
from datapunk.lib.tracing import TracingManager

@pytest.fixture
def manager_config():
    return QueueManagerConfig(
        name="test_manager",
        max_queues=10,
        max_queue_size=1000,
        message_ttl=3600,  # 1 hour
        default_priority=5,
        rebalance_interval=60,
        cleanup_interval=300
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
async def queue_manager(manager_config, mock_connection, mock_metrics, mock_tracing):
    manager = QueueManager(mock_connection, manager_config, mock_metrics, mock_tracing)
    await manager.initialize()
    return manager

@pytest.mark.asyncio
async def test_manager_initialization(queue_manager, manager_config, mock_connection):
    """Test queue manager initialization"""
    channel = await mock_connection.channel()
    
    # Verify exchange setup
    channel.declare_exchange.assert_called_with(
        manager_config.name,
        durable=True,
        arguments={
            'x-max-queues': manager_config.max_queues
        }
    )

@pytest.mark.asyncio
async def test_queue_creation(queue_manager, mock_connection):
    """Test queue creation and setup"""
    queue_name = "test_queue"
    
    # Create queue
    await queue_manager.create_queue(queue_name)
    
    # Verify queue creation
    channel = await mock_connection.channel()
    channel.declare_queue.assert_called_with(
        queue_name,
        durable=True,
        arguments={
            'x-max-length': queue_manager.config.max_queue_size,
            'x-message-ttl': queue_manager.config.message_ttl * 1000,
            'x-default-priority': queue_manager.config.default_priority
        }
    )
    
    # Verify metrics
    queue_manager.metrics.increment.assert_called_with(
        'queues_created_total',
        {'manager': queue_manager.config.name}
    )

@pytest.mark.asyncio
async def test_queue_deletion(queue_manager, mock_connection):
    """Test queue deletion"""
    queue_name = "test_queue"
    
    # Create and then delete queue
    await queue_manager.create_queue(queue_name)
    await queue_manager.delete_queue(queue_name)
    
    # Verify deletion
    channel = await mock_connection.channel()
    channel.queue_delete.assert_called_with(queue_name)
    
    # Verify metrics
    queue_manager.metrics.increment.assert_called_with(
        'queues_deleted_total',
        {'manager': queue_manager.config.name}
    )

@pytest.mark.asyncio
async def test_message_enqueue(queue_manager, mock_connection):
    """Test message enqueuing"""
    queue_name = "test_queue"
    message = {
        "id": "test-123",
        "data": "test data"
    }
    
    # Create queue and enqueue message
    await queue_manager.create_queue(queue_name)
    await queue_manager.enqueue(queue_name, message)
    
    # Verify message publishing
    channel = await mock_connection.channel()
    channel.default_exchange.publish.assert_called_once()
    
    # Verify message properties
    published_message = channel.default_exchange.publish.call_args[0][0]
    assert published_message.content_type == "application/json"
    assert published_message.delivery_mode == 2  # Persistent
    
    # Verify metrics
    queue_manager.metrics.increment.assert_called_with(
        'messages_enqueued_total',
        {'manager': queue_manager.config.name, 'queue': queue_name}
    )

@pytest.mark.asyncio
async def test_message_dequeue(queue_manager, mock_connection):
    """Test message dequeuing"""
    queue_name = "test_queue"
    
    # Setup mock message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.message_id = "test-123"
    
    # Create queue
    await queue_manager.create_queue(queue_name)
    
    # Setup dequeue callback
    callback = AsyncMock()
    await queue_manager.dequeue(queue_name, callback)
    
    # Get message handler
    channel = await mock_connection.channel()
    queue = await channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process message
    await handler(message)
    
    # Verify callback execution
    callback.assert_called_once_with('{"test": "data"}')
    
    # Verify metrics
    queue_manager.metrics.increment.assert_called_with(
        'messages_dequeued_total',
        {'manager': queue_manager.config.name, 'queue': queue_name}
    )

@pytest.mark.asyncio
async def test_queue_monitoring(queue_manager, mock_connection):
    """Test queue monitoring"""
    queue_name = "test_queue"
    
    # Create queue
    await queue_manager.create_queue(queue_name)
    
    # Setup mock queue size
    channel = await mock_connection.channel()
    queue = await channel.declare_queue()
    queue.declare.return_value = (0, 5, 0)  # message_count = 5
    
    # Monitor queue
    stats = await queue_manager.get_queue_stats(queue_name)
    
    # Verify metrics
    queue_manager.metrics.gauge.assert_called_with(
        'queue_size',
        5,
        {'manager': queue_manager.config.name, 'queue': queue_name}
    )

@pytest.mark.asyncio
async def test_queue_rebalancing(queue_manager, mock_connection):
    """Test queue rebalancing"""
    # Create multiple queues
    queues = ["queue1", "queue2", "queue3"]
    for queue_name in queues:
        await queue_manager.create_queue(queue_name)
    
    # Trigger rebalancing
    await queue_manager.rebalance_queues()
    
    # Verify rebalancing metrics
    queue_manager.metrics.increment.assert_called_with(
        'queue_rebalancing_total',
        {'manager': queue_manager.config.name}
    )

@pytest.mark.asyncio
async def test_queue_cleanup(queue_manager, mock_connection):
    """Test queue cleanup"""
    queue_name = "test_queue"
    
    # Create queue
    await queue_manager.create_queue(queue_name)
    
    # Trigger cleanup
    await queue_manager.cleanup_queues()
    
    # Verify cleanup metrics
    queue_manager.metrics.increment.assert_called_with(
        'queue_cleanup_total',
        {'manager': queue_manager.config.name}
    )

@pytest.mark.asyncio
async def test_error_handling(queue_manager, mock_connection):
    """Test error handling"""
    queue_name = "test_queue"
    message = {"test": "data"}
    
    # Setup failing channel
    channel = await mock_connection.channel()
    channel.default_exchange.publish.side_effect = Exception("Publishing failed")
    
    # Attempt to enqueue
    with pytest.raises(Exception):
        await queue_manager.enqueue(queue_name, message)
    
    # Verify error metrics
    queue_manager.metrics.increment.assert_called_with(
        'queue_errors_total',
        {'manager': queue_manager.config.name, 'queue': queue_name}
    )

@pytest.mark.asyncio
async def test_queue_purging(queue_manager, mock_connection):
    """Test queue purging"""
    queue_name = "test_queue"
    
    # Create queue
    await queue_manager.create_queue(queue_name)
    
    # Purge queue
    await queue_manager.purge_queue(queue_name)
    
    # Verify purge operation
    channel = await mock_connection.channel()
    channel.queue_purge.assert_called_with(queue_name)
    
    # Verify metrics
    queue_manager.metrics.increment.assert_called_with(
        'queue_purged_total',
        {'manager': queue_manager.config.name, 'queue': queue_name}
    )

@pytest.mark.asyncio
async def test_message_priority(queue_manager, mock_connection):
    """Test message priority handling"""
    queue_name = "test_queue"
    message = {"test": "data"}
    priority = 8
    
    # Create queue and enqueue message with priority
    await queue_manager.create_queue(queue_name)
    await queue_manager.enqueue(queue_name, message, priority=priority)
    
    # Verify message priority
    channel = await mock_connection.channel()
    published_message = channel.default_exchange.publish.call_args[0][0]
    assert published_message.priority == priority

@pytest.mark.asyncio
async def test_tracing_integration(queue_manager, mock_connection):
    """Test tracing integration"""
    queue_name = "test_queue"
    message = {
        "id": "test-123",
        "data": "test data"
    }
    
    # Enqueue message
    await queue_manager.create_queue(queue_name)
    await queue_manager.enqueue(queue_name, message)
    
    # Verify tracing attributes
    queue_manager.tracing.set_attribute.assert_any_call(
        'queue.name', queue_name
    )
    queue_manager.tracing.set_attribute.assert_any_call(
        'message.id', 'test-123'
    )