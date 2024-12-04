import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.processing.templates.streaming import (
    StreamingTemplate,
    StreamConfig,
    StreamProcessor,
    StreamResult,
    StreamError,
    WindowType
)

@pytest.fixture
def stream_config():
    return StreamConfig(
        name="test_stream",
        version="1.0.0",
        processors=[
            StreamProcessor(
                name="window_processor",
                type="window",
                config={
                    "window_type": WindowType.SLIDING,
                    "window_size": 60,  # seconds
                    "slide_interval": 10  # seconds
                }
            ),
            StreamProcessor(
                name="aggregate_processor",
                type="aggregate",
                config={
                    "functions": [
                        {"name": "avg", "field": "value"},
                        {"name": "max", "field": "value"}
                    ]
                }
            )
        ],
        error_handling={
            "max_retries": 3,
            "retry_delay": 1,
            "dead_letter_queue": "error_stream"
        }
    )

@pytest.fixture
def mock_stream():
    return AsyncMock()

@pytest.fixture
async def streaming_template(stream_config, mock_stream):
    template = StreamingTemplate(stream_config)
    template.stream = mock_stream
    await template.initialize()
    return template

@pytest.mark.asyncio
async def test_template_initialization(streaming_template, stream_config):
    """Test streaming template initialization"""
    assert streaming_template.config == stream_config
    assert streaming_template.is_initialized
    assert len(streaming_template.processors) == len(stream_config.processors)

@pytest.mark.asyncio
async def test_window_processing(streaming_template):
    """Test window-based stream processing"""
    # Generate test events
    events = [
        {"timestamp": datetime.now() - timedelta(seconds=i), "value": i}
        for i in range(100)
    ]
    
    # Process events through window
    window_results = await streaming_template.process_window(
        "window_processor",
        events
    )
    
    assert len(window_results) > 0
    assert all(isinstance(w, list) for w in window_results)  # Each window is a list
    assert all(len(w) <= 60 for w in window_results)  # Max window size

@pytest.mark.asyncio
async def test_aggregation_processing(streaming_template):
    """Test aggregation processing"""
    # Test data
    window_data = [
        {"value": 10},
        {"value": 20},
        {"value": 30}
    ]
    
    result = await streaming_template.process_aggregation(
        "aggregate_processor",
        window_data
    )
    
    assert result.aggregations["avg"]["value"] == 20.0
    assert result.aggregations["max"]["value"] == 30

@pytest.mark.asyncio
async def test_stream_processing_pipeline(streaming_template):
    """Test complete stream processing pipeline"""
    # Mock stream data
    events = [
        {"timestamp": datetime.now(), "value": i}
        for i in range(10)
    ]
    
    results = await streaming_template.process(events)
    
    assert results.success
    assert len(results.windows) > 0
    assert all(w.aggregations for w in results.windows)

@pytest.mark.asyncio
async def test_error_handling(streaming_template):
    """Test error handling in stream processing"""
    # Test with invalid data
    invalid_events = [
        {"timestamp": "invalid", "value": 1}
    ]
    
    with pytest.raises(StreamError):
        await streaming_template.process(invalid_events)
    
    # Test retry mechanism
    with patch.object(streaming_template, 'process_window') as mock_process:
        mock_process.side_effect = [
            StreamError("Processing error"),  # First attempt fails
            StreamError("Processing error"),  # Second attempt fails
            []  # Third attempt succeeds
        ]
        
        result = await streaming_template.process([{"timestamp": datetime.now(), "value": 1}])
        assert result.success
        assert mock_process.call_count == 3

@pytest.mark.asyncio
async def test_sliding_window(streaming_template):
    """Test sliding window behavior"""
    now = datetime.now()
    events = [
        {"timestamp": now - timedelta(seconds=i), "value": i}
        for i in range(100)
    ]
    
    windows = await streaming_template.create_sliding_windows(
        events,
        window_size=60,
        slide_interval=10
    )
    
    assert len(windows) > 0
    # Check overlap between consecutive windows
    for i in range(len(windows) - 1):
        common_events = set(str(e) for e in windows[i]).intersection(
            set(str(e) for e in windows[i + 1])
        )
        assert len(common_events) > 0  # Should have overlapping events

@pytest.mark.asyncio
async def test_tumbling_window(streaming_template):
    """Test tumbling window behavior"""
    now = datetime.now()
    events = [
        {"timestamp": now - timedelta(seconds=i), "value": i}
        for i in range(100)
    ]
    
    windows = await streaming_template.create_tumbling_windows(
        events,
        window_size=30
    )
    
    assert len(windows) > 0
    # Check no overlap between consecutive windows
    for i in range(len(windows) - 1):
        common_events = set(str(e) for e in windows[i]).intersection(
            set(str(e) for e in windows[i + 1])
        )
        assert len(common_events) == 0  # Should not have overlapping events

@pytest.mark.asyncio
async def test_session_window(streaming_template):
    """Test session window behavior"""
    # Create events with gaps
    events = []
    now = datetime.now()
    
    # First session
    for i in range(10):
        events.append({
            "timestamp": now - timedelta(seconds=i),
            "value": i
        })
    
    # Gap
    gap_start = now - timedelta(seconds=30)
    
    # Second session
    for i in range(10):
        events.append({
            "timestamp": gap_start - timedelta(seconds=i),
            "value": i + 10
        })
    
    windows = await streaming_template.create_session_windows(
        events,
        gap_threshold=20  # seconds
    )
    
    assert len(windows) == 2  # Should create two session windows

@pytest.mark.asyncio
async def test_watermark_handling(streaming_template):
    """Test watermark handling for late events"""
    now = datetime.now()
    events = [
        # On-time events
        {"timestamp": now - timedelta(seconds=1), "value": 1},
        {"timestamp": now - timedelta(seconds=2), "value": 2},
        # Late event
        {"timestamp": now - timedelta(minutes=5), "value": 3}
    ]
    
    watermark = now - timedelta(minutes=1)
    result = await streaming_template.process_with_watermark(events, watermark)
    
    assert len(result.late_events) == 1
    assert len(result.on_time_events) == 2

@pytest.mark.asyncio
async def test_stream_metrics(streaming_template):
    """Test stream processing metrics"""
    metrics = []
    streaming_template.set_metrics_callback(metrics.append)
    
    events = [
        {"timestamp": datetime.now(), "value": i}
        for i in range(10)
    ]
    
    await streaming_template.process(events)
    
    assert len(metrics) > 0
    assert any(m["type"] == "processing_latency" for m in metrics)
    assert any(m["type"] == "events_processed" for m in metrics)

@pytest.mark.asyncio
async def test_stream_hooks(streaming_template):
    """Test stream processing hooks"""
    pre_process = AsyncMock()
    post_process = AsyncMock()
    
    streaming_template.add_pre_process_hook(pre_process)
    streaming_template.add_post_process_hook(post_process)
    
    events = [{"timestamp": datetime.now(), "value": 1}]
    await streaming_template.process(events)
    
    pre_process.assert_called_once()
    post_process.assert_called_once()

@pytest.mark.asyncio
async def test_custom_aggregations(streaming_template):
    """Test custom aggregation functions"""
    # Add custom aggregation
    async def custom_agg(values):
        return sum(v * 2 for v in values)
    
    streaming_template.add_aggregation_function("double_sum", custom_agg)
    
    # Process data with custom aggregation
    window_data = [
        {"value": 1},
        {"value": 2},
        {"value": 3}
    ]
    
    result = await streaming_template.process_aggregation(
        "aggregate_processor",
        window_data,
        additional_functions=[{"name": "double_sum", "field": "value"}]
    )
    
    assert result.aggregations["double_sum"]["value"] == 12  # (1+2+3)*2 