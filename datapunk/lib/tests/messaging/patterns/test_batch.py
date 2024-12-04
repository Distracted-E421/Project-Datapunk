import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.messaging.patterns.batch import BatchProcessor, BatchConfig
from datapunk_shared.monitoring import MetricsClient
from datapunk.lib.tracing import TracingManager

@pytest.fixture
def batch_config():
    return BatchConfig(
        name="test_batch",
        batch_size=10,
        max_wait_time=5,  # seconds
        max_retries=3,
        retry_delay=1,
        error_threshold=0.2,  # 20% error rate threshold
        timeout=30  # seconds
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
async def batch_processor(batch_config, mock_connection, mock_metrics, mock_tracing):
    processor = BatchProcessor(mock_connection, batch_config, mock_metrics, mock_tracing)
    await processor.initialize()
    return processor

@pytest.mark.asyncio
async def test_batch_initialization(batch_processor, batch_config, mock_connection):
    """Test batch processor initialization"""
    channel = await mock_connection.channel()
    
    # Verify queue declaration
    channel.declare_queue.assert_called_with(
        batch_config.name,
        durable=True,
        arguments={
            'x-max-length': batch_config.batch_size * 2,  # Buffer size
            'x-message-ttl': batch_config.timeout * 1000
        }
    )

@pytest.mark.asyncio
async def test_message_collection(batch_processor, mock_connection):
    """Test message collection into batch"""
    messages = [
        {"id": f"test-{i}", "data": f"data-{i}"}
        for i in range(5)
    ]
    
    for message in messages:
        await batch_processor.add_message(message)
    
    # Verify messages were queued
    assert batch_processor.current_batch_size == 5
    
    # Verify metrics
    batch_processor.metrics.increment.assert_called_with(
        'batch_messages_queued_total',
        {'batch': batch_processor.config.name}
    )

@pytest.mark.asyncio
async def test_batch_processing(batch_processor, mock_connection):
    """Test batch processing execution"""
    # Setup test messages
    messages = [
        {"id": f"test-{i}", "data": f"data-{i}"}
        for i in range(batch_processor.config.batch_size)
    ]
    
    # Add messages to batch
    for message in messages:
        await batch_processor.add_message(message)
    
    # Setup mock processor
    processor = AsyncMock()
    
    # Process batch
    await batch_processor.process_batch(processor)
    
    # Verify processor was called with batch
    processor.assert_called_once()
    processed_messages = processor.call_args[0][0]
    assert len(processed_messages) == batch_processor.config.batch_size
    
    # Verify metrics
    batch_processor.metrics.increment.assert_any_call(
        'batch_processed_total',
        {'batch': batch_processor.config.name}
    )

@pytest.mark.asyncio
async def test_partial_batch_timeout(batch_processor, mock_connection):
    """Test processing of partial batch on timeout"""
    # Add fewer messages than batch size
    messages = [
        {"id": f"test-{i}", "data": f"data-{i}"}
        for i in range(5)  # Half of batch size
    ]
    
    for message in messages:
        await batch_processor.add_message(message)
    
    # Setup mock processor
    processor = AsyncMock()
    
    # Simulate timeout
    batch_processor.last_message_time = datetime.utcnow() - timedelta(
        seconds=batch_processor.config.max_wait_time + 1
    )
    
    # Process batch
    await batch_processor.process_batch(processor)
    
    # Verify processor was called with partial batch
    processor.assert_called_once()
    processed_messages = processor.call_args[0][0]
    assert len(processed_messages) == 5
    
    # Verify timeout metrics
    batch_processor.metrics.increment.assert_any_call(
        'batch_timeout_total',
        {'batch': batch_processor.config.name}
    )

@pytest.mark.asyncio
async def test_batch_error_handling(batch_processor, mock_connection):
    """Test batch processing error handling"""
    # Setup test messages
    messages = [
        {"id": f"test-{i}", "data": f"data-{i}"}
        for i in range(batch_processor.config.batch_size)
    ]
    
    for message in messages:
        await batch_processor.add_message(message)
    
    # Setup failing processor
    processor = AsyncMock(side_effect=Exception("Processing failed"))
    
    # Process batch
    with pytest.raises(Exception):
        await batch_processor.process_batch(processor)
    
    # Verify error metrics
    batch_processor.metrics.increment.assert_any_call(
        'batch_errors_total',
        {'batch': batch_processor.config.name}
    )

@pytest.mark.asyncio
async def test_error_threshold_monitoring(batch_processor, mock_connection):
    """Test error threshold monitoring"""
    # Setup test messages
    messages = [
        {"id": f"test-{i}", "data": f"data-{i}"}
        for i in range(10)
    ]
    
    # Simulate error rate above threshold
    batch_processor.error_count = 3  # 30% error rate
    batch_processor.total_processed = 10
    
    # Verify error threshold alert
    await batch_processor.check_error_threshold()
    
    batch_processor.metrics.increment.assert_any_call(
        'batch_error_threshold_exceeded_total',
        {'batch': batch_processor.config.name}
    )

@pytest.mark.asyncio
async def test_batch_retry_mechanism(batch_processor, mock_connection):
    """Test batch retry mechanism"""
    # Setup test messages
    messages = [
        {"id": f"test-{i}", "data": f"data-{i}"}
        for i in range(5)
    ]
    
    for message in messages:
        await batch_processor.add_message(message)
    
    # Setup processor that fails twice then succeeds
    processor = AsyncMock()
    processor.side_effect = [
        Exception("First attempt"),
        Exception("Second attempt"),
        "Success"
    ]
    
    # Process batch
    result = await batch_processor.process_with_retry(processor)
    assert result == "Success"
    
    # Verify retry metrics
    batch_processor.metrics.increment.assert_any_call(
        'batch_retries_total',
        {'batch': batch_processor.config.name}
    )

@pytest.mark.asyncio
async def test_batch_monitoring(batch_processor, mock_connection):
    """Test batch processing monitoring"""
    # Setup test messages
    messages = [
        {"id": f"test-{i}", "data": f"data-{i}"}
        for i in range(batch_processor.config.batch_size)
    ]
    
    start_time = datetime.utcnow()
    
    for message in messages:
        await batch_processor.add_message(message)
    
    processor = AsyncMock()
    await batch_processor.process_batch(processor)
    
    # Verify monitoring metrics
    batch_processor.metrics.gauge.assert_any_call(
        'batch_size',
        batch_processor.config.batch_size,
        {'batch': batch_processor.config.name}
    )
    
    batch_processor.metrics.histogram.assert_any_call(
        'batch_processing_duration_seconds',
        {'batch': batch_processor.config.name},
        value=pytest.approx((datetime.utcnow() - start_time).total_seconds(), rel=1e-1)
    )

@pytest.mark.asyncio
async def test_tracing_integration(batch_processor, mock_connection):
    """Test tracing context integration"""
    # Setup test message
    message = {"id": "test-123", "data": "test-data"}
    
    await batch_processor.add_message(message)
    
    # Verify tracing attributes
    batch_processor.tracing.set_attribute.assert_any_call(
        'batch.message_id',
        'test-123'
    )
    batch_processor.tracing.set_attribute.assert_any_call(
        'batch.size',
        1
    )