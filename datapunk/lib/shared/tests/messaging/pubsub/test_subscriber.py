import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.messaging.pubsub.subscriber import Subscriber, SubscriberConfig
from datapunk_shared.monitoring import MetricsClient
from datapunk_shared.tracing import TracingManager

@pytest.fixture
def subscriber_config():
    return SubscriberConfig(
        name="test_subscriber",
        topics=["test.topic.1", "test.topic.2"],
        max_retries=3,
        retry_delay=1,
        batch_size=10,
        prefetch_count=100,
        timeout=30
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
async def subscriber(subscriber_config, mock_connection, mock_metrics, mock_tracing):
    subscriber = Subscriber(mock_connection, subscriber_config, mock_metrics, mock_tracing)
    await subscriber.initialize()
    return subscriber

@pytest.mark.asyncio
async def test_subscriber_initialization(subscriber, subscriber_config, mock_connection):
    """Test subscriber initialization and setup"""
    channel = await mock_connection.channel()
    
    # Verify channel setup
    channel.set_qos.assert_called_with(prefetch_count=subscriber_config.prefetch_count)
    
    # Verify exchange declarations
    for topic in subscriber_config.topics:
        channel.declare_exchange.assert_any_call(
            topic,
            durable=True
        )
    
    # Verify queue declarations
    assert channel.declare_queue.call_count == len(subscriber_config.topics)

@pytest.mark.asyncio
async def test_message_subscription(subscriber, mock_connection):
    """Test message subscription handling"""
    # Setup mock message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.routing_key = "test.topic.1"
    message.message_id = "test-123"
    
    # Setup mock callback
    callback = AsyncMock()
    
    # Start subscription
    await subscriber.subscribe(callback)
    
    # Get message handler
    channel = await mock_connection.channel()
    queue = await channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process test message
    await handler(message)
    
    # Verify message processing
    callback.assert_called_once_with('{"test": "data"}', "test.topic.1")
    subscriber.metrics.increment.assert_called_with(
        'messages_processed_total',
        {'subscriber': subscriber.config.name, 'topic': "test.topic.1"}
    )

@pytest.mark.asyncio
async def test_message_filtering(subscriber, mock_connection):
    """Test message filtering"""
    # Setup message filter
    def filter_func(message):
        data = message.get("test")
        return data == "valid"
    
    # Setup messages
    valid_message = AsyncMock()
    valid_message.body = b'{"test": "valid"}'
    valid_message.routing_key = "test.topic.1"
    
    invalid_message = AsyncMock()
    invalid_message.body = b'{"test": "invalid"}'
    invalid_message.routing_key = "test.topic.1"
    
    # Setup callback
    callback = AsyncMock()
    
    # Start subscription with filter
    await subscriber.subscribe(callback, message_filter=filter_func)
    
    # Get message handler
    channel = await mock_connection.channel()
    queue = await channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process messages
    await handler(valid_message)
    await handler(invalid_message)
    
    # Verify only valid message was processed
    assert callback.call_count == 1
    callback.assert_called_with('{"test": "valid"}', "test.topic.1")

@pytest.mark.asyncio
async def test_error_handling(subscriber, mock_connection):
    """Test error handling in message processing"""
    # Setup failing callback
    callback = AsyncMock(side_effect=Exception("Processing failed"))
    
    # Setup message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.routing_key = "test.topic.1"
    message.message_id = "test-123"
    
    # Start subscription
    await subscriber.subscribe(callback)
    
    # Get message handler
    channel = await mock_connection.channel()
    queue = await channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process message
    with pytest.raises(Exception):
        await handler(message)
    
    # Verify error metrics
    subscriber.metrics.increment.assert_called_with(
        'message_errors_total',
        {'subscriber': subscriber.config.name, 'topic': "test.topic.1"}
    )

@pytest.mark.asyncio
async def test_batch_processing(subscriber, mock_connection):
    """Test batch message processing"""
    # Setup batch of messages
    messages = []
    for i in range(subscriber.config.batch_size):
        message = AsyncMock()
        message.body = f'{{"id": "test-{i}"}}'.encode()
        message.routing_key = "test.topic.1"
        message.message_id = f"msg-{i}"
        messages.append(message)
    
    # Setup batch callback
    batch_callback = AsyncMock()
    
    # Start batch subscription
    await subscriber.subscribe_batch(batch_callback)
    
    # Get batch handler
    channel = await mock_connection.channel()
    queue = await channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process batch
    for message in messages:
        await handler(message)
    
    # Verify batch processing
    batch_callback.assert_called_once()
    processed_batch = batch_callback.call_args[0][0]
    assert len(processed_batch) == subscriber.config.batch_size

@pytest.mark.asyncio
async def test_retry_mechanism(subscriber, mock_connection):
    """Test message retry mechanism"""
    # Setup failing callback that succeeds on third try
    callback = AsyncMock()
    callback.side_effect = [
        Exception("First attempt"),
        Exception("Second attempt"),
        None  # Success
    ]
    
    # Setup message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.routing_key = "test.topic.1"
    message.message_id = "test-123"
    message.headers = {'retry_count': 0}
    
    # Start subscription
    await subscriber.subscribe(callback)
    
    # Get message handler
    channel = await mock_connection.channel()
    queue = await channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process message
    await handler(message)
    
    # Verify retry metrics
    subscriber.metrics.increment.assert_any_call(
        'message_retries_total',
        {'subscriber': subscriber.config.name, 'topic': "test.topic.1"}
    )

@pytest.mark.asyncio
async def test_subscription_management(subscriber, mock_connection):
    """Test subscription management"""
    # Setup callbacks
    callback1 = AsyncMock()
    callback2 = AsyncMock()
    
    # Subscribe to different topics
    await subscriber.subscribe(callback1, topics=["test.topic.1"])
    await subscriber.subscribe(callback2, topics=["test.topic.2"])
    
    # Verify subscription setup
    channel = await mock_connection.channel()
    assert channel.declare_queue.call_count == 2
    
    # Test unsubscribe
    await subscriber.unsubscribe(["test.topic.1"])
    
    # Verify queue deletion
    channel.queue_delete.assert_called_once()

@pytest.mark.asyncio
async def test_monitoring_integration(subscriber, mock_connection):
    """Test monitoring metrics integration"""
    # Setup message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.routing_key = "test.topic.1"
    message.message_id = "test-123"
    
    # Setup callback
    callback = AsyncMock()
    
    # Start subscription
    await subscriber.subscribe(callback)
    
    # Get message handler
    channel = await mock_connection.channel()
    queue = await channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process message
    start_time = datetime.utcnow()
    await handler(message)
    
    # Verify metrics
    subscriber.metrics.increment.assert_any_call(
        'messages_processed_total',
        {'subscriber': subscriber.config.name, 'topic': "test.topic.1"}
    )
    
    subscriber.metrics.histogram.assert_called_with(
        'message_processing_duration_seconds',
        {'subscriber': subscriber.config.name, 'topic': "test.topic.1"},
        value=pytest.approx((datetime.utcnow() - start_time).total_seconds(), rel=1e-1)
    )

@pytest.mark.asyncio
async def test_tracing_integration(subscriber, mock_connection):
    """Test tracing context integration"""
    # Setup message
    message = AsyncMock()
    message.body = b'{"test": "data"}'
    message.routing_key = "test.topic.1"
    message.message_id = "test-123"
    message.correlation_id = "correlation-123"
    
    # Setup callback
    callback = AsyncMock()
    
    # Start subscription
    await subscriber.subscribe(callback)
    
    # Get message handler
    channel = await mock_connection.channel()
    queue = await channel.declare_queue()
    handler = queue.consume.call_args[0][0]
    
    # Process message
    await handler(message)
    
    # Verify tracing attributes
    subscriber.tracing.set_attribute.assert_any_call(
        'message.id', 'test-123'
    )
    subscriber.tracing.set_attribute.assert_any_call(
        'message.topic', 'test.topic.1'
    )
    subscriber.tracing.set_attribute.assert_any_call(
        'message.correlation_id', 'correlation-123'
    )