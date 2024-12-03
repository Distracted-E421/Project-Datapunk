import pytest
import json
import aio_pika
from unittest.mock import AsyncMock, MagicMock, patch
from datapunk_shared.messaging import MessageBroker

@pytest.fixture
def broker_config():
    return {
        'host': 'localhost',
        'port': 5672,
        'user': 'guest',
        'password': 'guest',
        'vhost': '/',
        'timeout': 5.0,
        'prefetch_count': 100
    }

@pytest.fixture
def mock_connection():
    connection = AsyncMock()
    channel = AsyncMock()
    connection.channel.return_value = channel
    return connection, channel

@pytest.fixture
def mock_queue():
    queue = AsyncMock()
    queue.name = 'test_queue'
    return queue

@pytest.fixture
async def message_broker(broker_config):
    broker = MessageBroker(broker_config)
    yield broker
    await broker.close()

@pytest.mark.asyncio
async def test_broker_initialization(message_broker, mock_connection):
    """Test message broker initialization and connection setup"""
    connection, channel = mock_connection
    
    with patch('aio_pika.connect_robust', return_value=connection):
        await message_broker.initialize()
        
        # Verify connection setup
        aio_pika.connect_robust.assert_called_once_with(
            host='localhost',
            port=5672,
            login='guest',
            password='guest',
            virtualhost='/',
            timeout=5.0
        )
        
        # Verify channel setup and QoS
        connection.channel.assert_called_once()
        channel.set_qos.assert_called_once_with(prefetch_count=100)

@pytest.mark.asyncio
async def test_broker_initialization_retry(message_broker):
    """Test broker initialization with connection retry"""
    with patch('aio_pika.connect_robust') as mock_connect:
        mock_connect.side_effect = [
            aio_pika.AMQPException("Connection failed"),
            AsyncMock()  # Succeed on second attempt
        ]
        
        await message_broker.initialize()
        assert mock_connect.call_count == 2

@pytest.mark.asyncio
async def test_broker_close(message_broker, mock_connection):
    """Test graceful broker shutdown"""
    connection, channel = mock_connection
    message_broker.connection = connection
    message_broker.channel = channel
    
    await message_broker.close()
    
    channel.close.assert_called_once()
    connection.close.assert_called_once()

@pytest.mark.asyncio
async def test_declare_queue(message_broker, mock_connection, mock_queue):
    """Test queue declaration with durability options"""
    connection, channel = mock_connection
    channel.declare_queue.return_value = mock_queue
    message_broker.channel = channel
    
    queue = await message_broker.declare_queue("test_queue", durable=True)
    
    channel.declare_queue.assert_called_once_with(
        name="test_queue",
        durable=True,
        auto_delete=False
    )
    assert queue == mock_queue
    assert message_broker.queues["test_queue"] == mock_queue

@pytest.mark.asyncio
async def test_declare_queue_uninitialized(message_broker):
    """Test queue declaration when broker is not initialized"""
    with pytest.raises(RuntimeError) as exc_info:
        await message_broker.declare_queue("test_queue")
    assert "Message broker not initialized" in str(exc_info.value)

@pytest.mark.asyncio
async def test_declare_queue_retry(message_broker, mock_connection, mock_queue):
    """Test queue declaration with retry on failure"""
    connection, channel = mock_connection
    channel.declare_queue.side_effect = [
        aio_pika.AMQPException("Queue declaration failed"),
        mock_queue  # Succeed on second attempt
    ]
    message_broker.channel = channel
    
    queue = await message_broker.declare_queue("test_queue")
    
    assert channel.declare_queue.call_count == 2
    assert queue == mock_queue

@pytest.mark.asyncio
async def test_publish_message(message_broker, mock_connection):
    """Test message publishing with persistence"""
    connection, channel = mock_connection
    exchange = AsyncMock()
    channel.default_exchange = exchange
    message_broker.channel = channel
    
    test_message = {"key": "value"}
    await message_broker.publish("test_queue", test_message)
    
    # Verify message was published with correct properties
    exchange.publish.assert_called_once()
    call_args = exchange.publish.call_args[0]
    message = call_args[0]
    
    assert message.body == json.dumps(test_message).encode()
    assert message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT
    assert call_args[1] == "test_queue"  # routing key

@pytest.mark.asyncio
async def test_publish_uninitialized(message_broker):
    """Test message publishing when broker is not initialized"""
    with pytest.raises(RuntimeError) as exc_info:
        await message_broker.publish("test_queue", {"key": "value"})
    assert "Message broker not initialized" in str(exc_info.value)

@pytest.mark.asyncio
async def test_publish_retry(message_broker, mock_connection):
    """Test message publishing with retry on failure"""
    connection, channel = mock_connection
    exchange = AsyncMock()
    exchange.publish.side_effect = [
        aio_pika.AMQPException("Publish failed"),
        None  # Succeed on second attempt
    ]
    channel.default_exchange = exchange
    message_broker.channel = channel
    
    await message_broker.publish("test_queue", {"key": "value"})
    assert exchange.publish.call_count == 2

@pytest.mark.asyncio
async def test_consume_messages(message_broker, mock_connection, mock_queue):
    """Test message consumption setup"""
    connection, channel = mock_connection
    message_broker.channel = channel
    message_broker.queues["test_queue"] = mock_queue
    
    callback = AsyncMock()
    await message_broker.consume("test_queue", callback)
    
    mock_queue.consume.assert_called_once()

@pytest.mark.asyncio
async def test_consume_with_auto_declare(message_broker, mock_connection, mock_queue):
    """Test message consumption with automatic queue declaration"""
    connection, channel = mock_connection
    channel.declare_queue.return_value = mock_queue
    message_broker.channel = channel
    
    callback = AsyncMock()
    await message_broker.consume("test_queue", callback)
    
    channel.declare_queue.assert_called_once()
    mock_queue.consume.assert_called_once()

@pytest.mark.asyncio
async def test_message_processing(message_broker, mock_connection, mock_queue):
    """Test message processing with callback execution"""
    connection, channel = mock_connection
    message_broker.channel = channel
    message_broker.queues["test_queue"] = mock_queue
    
    # Create a test message
    test_data = {"key": "value"}
    message = AsyncMock()
    message.body = json.dumps(test_data).encode()
    
    # Capture the process_message function
    await message_broker.consume("test_queue", AsyncMock())
    process_message = mock_queue.consume.call_args[0][0]
    
    # Test message processing
    await process_message(message)
    
    # Verify message was processed
    message.process.assert_called_once()

@pytest.mark.asyncio
async def test_message_processing_error(message_broker, mock_connection, mock_queue):
    """Test error handling during message processing"""
    connection, channel = mock_connection
    message_broker.channel = channel
    message_broker.queues["test_queue"] = mock_queue
    
    # Create a callback that raises an exception
    async def failing_callback(data):
        raise ValueError("Processing error")
    
    # Create a test message
    message = AsyncMock()
    message.body = json.dumps({"key": "value"}).encode()
    
    # Capture the process_message function
    await message_broker.consume("test_queue", failing_callback)
    process_message = mock_queue.consume.call_args[0][0]
    
    # Test message processing with error
    with patch('builtins.print') as mock_print:
        await process_message(message)
        
        # Verify error was handled
        mock_print.assert_called_once()
        assert "Processing error" in mock_print.call_args[0][0] 