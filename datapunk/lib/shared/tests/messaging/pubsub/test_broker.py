import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.messaging.pubsub.broker import MessageBroker, BrokerConfig
from datapunk_shared.monitoring import MetricsClient
from datapunk_shared.tracing import TracingManager

@pytest.fixture
def broker_config():
    return BrokerConfig(
        name="test_broker",
        max_message_size=1024 * 1024,  # 1MB
        max_queue_size=1000,
        message_ttl=3600,  # 1 hour
        persistence_enabled=True,
        replication_factor=2,
        sync_interval=5
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
async def broker(broker_config, mock_connection, mock_metrics, mock_tracing):
    broker = MessageBroker(mock_connection, broker_config, mock_metrics, mock_tracing)
    await broker.initialize()
    return broker

@pytest.mark.asyncio
async def test_broker_initialization(broker, broker_config, mock_connection):
    """Test broker initialization and setup"""
    channel = await mock_connection.channel()
    
    # Verify exchange setup
    channel.declare_exchange.assert_called_with(
        broker_config.name,
        durable=True,
        arguments={
            'x-max-length': broker_config.max_queue_size,
            'x-message-ttl': broker_config.message_ttl * 1000
        }
    )

@pytest.mark.asyncio
async def test_message_publishing(broker, mock_connection):
    """Test message publishing"""
    # Setup test message
    message = {
        "id": "test-123",
        "data": "test data",
        "timestamp": datetime.utcnow().isoformat()
    }
    routing_key = "test.topic"
    
    # Publish message
    await broker.publish(message, routing_key)
    
    # Verify message was published
    channel = await mock_connection.channel()
    channel.default_exchange.publish.assert_called_once()
    
    # Verify message properties
    published_message = channel.default_exchange.publish.call_args[0][0]
    assert published_message.content_type == "application/json"
    assert published_message.delivery_mode == 2  # Persistent
    
    # Verify metrics
    broker.metrics.increment.assert_called_with(
        'messages_published_total',
        {'broker': broker.config.name, 'topic': routing_key}
    )

@pytest.mark.asyncio
async def test_message_routing(broker, mock_connection):
    """Test message routing to multiple subscribers"""
    # Setup test message
    message = {
        "id": "test-123",
        "data": "test data"
    }
    
    # Setup multiple routing keys
    routing_keys = ["test.topic.1", "test.topic.2"]
    
    # Publish to multiple routes
    for routing_key in routing_keys:
        await broker.publish(message, routing_key)
    
    # Verify routing
    channel = await mock_connection.channel()
    assert channel.default_exchange.publish.call_count == len(routing_keys)
    
    # Verify routing keys
    for i, routing_key in enumerate(routing_keys):
        call_args = channel.default_exchange.publish.call_args_list[i]
        assert call_args[1]['routing_key'] == routing_key

@pytest.mark.asyncio
async def test_message_validation(broker, mock_connection):
    """Test message validation"""
    # Test oversized message
    large_message = {
        "data": "x" * (broker.config.max_message_size + 1)
    }
    
    with pytest.raises(ValueError):
        await broker.publish(large_message, "test.topic")
    
    # Verify no message was published
    channel = await mock_connection.channel()
    channel.default_exchange.publish.assert_not_called()

@pytest.mark.asyncio
async def test_persistence_handling(broker, mock_connection):
    """Test message persistence handling"""
    # Setup test message
    message = {
        "id": "test-123",
        "data": "test data"
    }
    
    # Publish with persistence
    await broker.publish(message, "test.topic", persistent=True)
    
    # Verify persistence settings
    channel = await mock_connection.channel()
    published_message = channel.default_exchange.publish.call_args[0][0]
    assert published_message.delivery_mode == 2  # Persistent
    
    # Publish without persistence
    await broker.publish(message, "test.topic", persistent=False)
    published_message = channel.default_exchange.publish.call_args[0][0]
    assert published_message.delivery_mode == 1  # Non-persistent

@pytest.mark.asyncio
async def test_message_expiration(broker, mock_connection):
    """Test message expiration handling"""
    # Setup test message
    message = {
        "id": "test-123",
        "data": "test data"
    }
    
    # Publish with custom expiration
    expiration = 60  # 1 minute
    await broker.publish(message, "test.topic", expiration=expiration)
    
    # Verify expiration setting
    channel = await mock_connection.channel()
    published_message = channel.default_exchange.publish.call_args[0][0]
    assert published_message.expiration == str(expiration * 1000)  # Milliseconds

@pytest.mark.asyncio
async def test_priority_handling(broker, mock_connection):
    """Test message priority handling"""
    # Setup test messages with different priorities
    messages = [
        {"id": f"test-{i}", "priority": i}
        for i in range(3)
    ]
    
    # Publish messages with priorities
    for message in messages:
        await broker.publish(
            message,
            "test.topic",
            priority=message['priority']
        )
    
    # Verify priority settings
    channel = await mock_connection.channel()
    for i, message in enumerate(messages):
        published_message = channel.default_exchange.publish.call_args_list[i][0][0]
        assert published_message.priority == message['priority']

@pytest.mark.asyncio
async def test_error_handling(broker, mock_connection):
    """Test error handling during publishing"""
    # Setup failing channel
    channel = await mock_connection.channel()
    channel.default_exchange.publish.side_effect = Exception("Publishing failed")
    
    # Attempt to publish
    message = {"id": "test-123", "data": "test data"}
    
    with pytest.raises(Exception):
        await broker.publish(message, "test.topic")
    
    # Verify error metrics
    broker.metrics.increment.assert_called_with(
        'publish_errors_total',
        {'broker': broker.config.name, 'topic': "test.topic"}
    )

@pytest.mark.asyncio
async def test_monitoring_integration(broker, mock_connection):
    """Test monitoring metrics integration"""
    # Setup test message
    message = {
        "id": "test-123",
        "data": "test data"
    }
    
    # Publish message
    start_time = datetime.utcnow()
    await broker.publish(message, "test.topic")
    
    # Verify metrics
    broker.metrics.increment.assert_called_with(
        'messages_published_total',
        {'broker': broker.config.name, 'topic': "test.topic"}
    )
    
    broker.metrics.histogram.assert_called_with(
        'message_size_bytes',
        {'broker': broker.config.name, 'topic': "test.topic"},
        value=pytest.approx(len(str(message)))
    )

@pytest.mark.asyncio
async def test_replication_handling(broker, mock_connection):
    """Test message replication handling"""
    # Setup test message
    message = {
        "id": "test-123",
        "data": "test data"
    }
    
    # Publish with replication
    await broker.publish(message, "test.topic", replicate=True)
    
    # Verify replication headers
    channel = await mock_connection.channel()
    published_message = channel.default_exchange.publish.call_args[0][0]
    assert published_message.headers.get('x-replication-factor') == broker.config.replication_factor

@pytest.mark.asyncio
async def test_tracing_integration(broker, mock_connection):
    """Test tracing context integration"""
    # Setup test message
    message = {
        "id": "test-123",
        "data": "test data"
    }
    correlation_id = "correlation-123"
    
    # Publish with tracing
    await broker.publish(message, "test.topic", correlation_id=correlation_id)
    
    # Verify tracing attributes
    broker.tracing.set_attribute.assert_any_call(
        'message.id', 'test-123'
    )
    broker.tracing.set_attribute.assert_any_call(
        'message.topic', 'test.topic'
    )
    broker.tracing.set_attribute.assert_any_call(
        'message.correlation_id', correlation_id
    )

@pytest.mark.asyncio
async def test_queue_management(broker, mock_connection):
    """Test queue management operations"""
    # Test queue creation
    await broker.create_queue("test_queue")
    
    channel = await mock_connection.channel()
    channel.declare_queue.assert_called_with(
        "test_queue",
        durable=True,
        arguments={
            'x-max-length': broker.config.max_queue_size,
            'x-message-ttl': broker.config.message_ttl * 1000
        }
    )
    
    # Test queue deletion
    await broker.delete_queue("test_queue")
    channel.queue_delete.assert_called_with("test_queue")