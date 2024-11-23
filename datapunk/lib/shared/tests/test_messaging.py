import pytest
from datetime import datetime
import json
from datapunk_shared.messaging import MessageQueue, MessageQueueError

@pytest.fixture
async def message_queue(config, metrics, rabbitmq_connection):
    """Create message queue instance"""
    queue = MessageQueue(config, metrics)
    queue.connection = rabbitmq_connection
    queue.channel = await rabbitmq_connection.channel()
    return queue

@pytest.mark.asyncio
async def test_publish_subscribe(message_queue):
    """Test message publishing and subscribing"""
    exchange_name = "test_exchange"
    routing_key = "test.route"
    test_message = {"test": "data"}
    received_messages = []
    
    # Create subscriber
    async def message_handler(message):
        received_messages.append(message)
    
    # Subscribe
    await message_queue.subscribe(
        exchange_name,
        routing_key,
        message_handler
    )
    
    # Publish message
    await message_queue.publish(
        exchange_name,
        routing_key,
        test_message
    )
    
    # Wait for message processing
    await asyncio.sleep(0.1)
    
    # Verify message was received
    assert len(received_messages) == 1
    assert received_messages[0]["payload"] == test_message
    assert "metadata" in received_messages[0]
    assert "timestamp" in received_messages[0]["metadata"]

@pytest.mark.asyncio
async def test_message_priority(message_queue):
    """Test message priority handling"""
    exchange_name = "test_priority"
    routing_key = "test.priority"
    received_messages = []
    
    # Create subscriber
    async def message_handler(message):
        received_messages.append(message)
    
    # Subscribe
    await message_queue.subscribe(
        exchange_name,
        routing_key,
        message_handler
    )
    
    # Publish messages with different priorities
    await message_queue.publish(
        exchange_name,
        routing_key,
        {"priority": "low"},
        priority=1
    )
    
    await message_queue.publish(
        exchange_name,
        routing_key,
        {"priority": "high"},
        priority=5
    )
    
    # Wait for message processing
    await asyncio.sleep(0.1)
    
    # Verify messages were received in priority order
    assert len(received_messages) == 2
    assert received_messages[0]["payload"]["priority"] == "high"
    assert received_messages[1]["payload"]["priority"] == "low"

@pytest.mark.asyncio
async def test_message_error_handling(message_queue):
    """Test error handling in message processing"""
    exchange_name = "test_error"
    routing_key = "test.error"
    error_count = 0
    
    # Create error-throwing handler
    async def error_handler(message):
        nonlocal error_count
        error_count += 1
        raise Exception("Test error")
    
    # Subscribe
    await message_queue.subscribe(
        exchange_name,
        routing_key,
        error_handler
    )
    
    # Publish message
    await message_queue.publish(
        exchange_name,
        routing_key,
        {"trigger": "error"}
    )
    
    # Wait for message processing and requeue
    await asyncio.sleep(0.2)
    
    # Verify message was requeued and processed again
    assert error_count > 1 