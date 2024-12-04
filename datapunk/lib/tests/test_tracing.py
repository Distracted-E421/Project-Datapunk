import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk.lib.tracing import (
    TracingManager,
    TracingConfig,
    Span,
    SpanContext,
    TracingError
)

@pytest.fixture
def tracing_config():
    return TracingConfig(
        name="test_tracer",
        exporters=[
            {
                "name": "jaeger",
                "type": "jaeger",
                "host": "localhost",
                "port": 6831
            },
            {
                "name": "zipkin",
                "type": "zipkin",
                "endpoint": "http://localhost:9411/api/v2/spans"
            }
        ],
        samplers=[
            {
                "name": "probability",
                "type": "probability",
                "rate": 0.1
            },
            {
                "name": "rate_limiting",
                "type": "rate_limiting",
                "max_traces_per_second": 100
            }
        ],
        propagation={
            "formats": ["b3", "w3c"],
            "baggage_prefix": "dp-"
        },
        metrics_enabled=True
    )

@pytest.fixture
async def tracing_manager(tracing_config):
    manager = TracingManager(tracing_config)
    await manager.initialize()
    return manager

@pytest.mark.asyncio
async def test_manager_initialization(tracing_manager, tracing_config):
    """Test tracing manager initialization"""
    assert tracing_manager.config == tracing_config
    assert tracing_manager.is_initialized
    assert len(tracing_manager.exporters) == len(tracing_config.exporters)
    assert len(tracing_manager.samplers) == len(tracing_config.samplers)

@pytest.mark.asyncio
async def test_span_creation(tracing_manager):
    """Test span creation and management"""
    # Create root span
    root_span = await tracing_manager.start_span(
        name="test_operation",
        attributes={
            "service.name": "test_service",
            "http.method": "GET"
        }
    )
    
    assert root_span.name == "test_operation"
    assert root_span.parent_id is None
    assert root_span.trace_id is not None
    
    # Create child span
    child_span = await tracing_manager.start_span(
        name="child_operation",
        parent=root_span
    )
    
    assert child_span.parent_id == root_span.span_id
    assert child_span.trace_id == root_span.trace_id

@pytest.mark.asyncio
async def test_span_context(tracing_manager):
    """Test span context management"""
    # Create span with context
    context = SpanContext(
        trace_id="test-trace-id",
        span_id="test-span-id",
        baggage={
            "user_id": "123",
            "request_id": "abc"
        }
    )
    
    span = await tracing_manager.start_span(
        name="context_operation",
        context=context
    )
    
    assert span.trace_id == context.trace_id
    assert span.baggage == context.baggage

@pytest.mark.asyncio
async def test_span_attributes(tracing_manager):
    """Test span attribute management"""
    span = await tracing_manager.start_span("test_operation")
    
    # Add attributes
    await span.set_attribute("http.status_code", 200)
    await span.set_attributes({
        "http.url": "http://example.com",
        "http.method": "POST"
    })
    
    assert span.attributes["http.status_code"] == 200
    assert "http.url" in span.attributes
    assert "http.method" in span.attributes

@pytest.mark.asyncio
async def test_span_events(tracing_manager):
    """Test span event recording"""
    span = await tracing_manager.start_span("test_operation")
    
    # Record events
    await span.add_event(
        name="cache_miss",
        attributes={"key": "user_123"}
    )
    
    await span.add_event(
        name="db_query",
        attributes={"query_id": "select_1"}
    )
    
    assert len(span.events) == 2
    assert span.events[0]["name"] == "cache_miss"
    assert span.events[1]["name"] == "db_query"

@pytest.mark.asyncio
async def test_span_status(tracing_manager):
    """Test span status management"""
    span = await tracing_manager.start_span("test_operation")
    
    # Set success status
    await span.set_status("ok")
    assert span.status == "ok"
    
    # Set error status with description
    await span.set_status(
        "error",
        description="Database connection failed"
    )
    assert span.status == "error"
    assert span.status_description is not None

@pytest.mark.asyncio
async def test_trace_sampling(tracing_manager):
    """Test trace sampling"""
    sampled_spans = []
    not_sampled_spans = []
    
    # Create multiple spans
    for _ in range(100):
        span = await tracing_manager.start_span("test_operation")
        if span.is_sampled:
            sampled_spans.append(span)
        else:
            not_sampled_spans.append(span)
    
    # Verify sampling rate
    sample_rate = len(sampled_spans) / 100
    assert 0.05 <= sample_rate <= 0.15  # Allow for some variance

@pytest.mark.asyncio
async def test_trace_export(tracing_manager):
    """Test trace export"""
    exported_spans = []
    
    # Mock exporter
    class MockExporter:
        async def export(self, spans):
            exported_spans.extend(spans)
    
    tracing_manager.add_exporter("mock", MockExporter())
    
    # Create and end some spans
    spans = []
    for i in range(5):
        span = await tracing_manager.start_span(f"operation_{i}")
        await span.end()
        spans.append(span)
    
    # Export spans
    await tracing_manager.export_spans(spans)
    
    assert len(exported_spans) == 5

@pytest.mark.asyncio
async def test_context_propagation(tracing_manager):
    """Test context propagation"""
    # Create span with context
    parent_span = await tracing_manager.start_span("parent_operation")
    
    # Extract context
    context_carrier = {}
    await tracing_manager.inject_context(parent_span.context, context_carrier)
    
    # Create new span with extracted context
    extracted_context = await tracing_manager.extract_context(context_carrier)
    child_span = await tracing_manager.start_span(
        "child_operation",
        context=extracted_context
    )
    
    assert child_span.trace_id == parent_span.trace_id
    assert child_span.parent_id == parent_span.span_id

@pytest.mark.asyncio
async def test_baggage_propagation(tracing_manager):
    """Test baggage propagation"""
    # Create span with baggage
    span = await tracing_manager.start_span(
        "test_operation",
        baggage={
            "user_id": "123",
            "tenant_id": "abc"
        }
    )
    
    # Extract and inject baggage
    carrier = {}
    await tracing_manager.inject_baggage(span.baggage, carrier)
    extracted_baggage = await tracing_manager.extract_baggage(carrier)
    
    assert extracted_baggage["user_id"] == "123"
    assert extracted_baggage["tenant_id"] == "abc"

@pytest.mark.asyncio
async def test_error_handling(tracing_manager):
    """Test error handling"""
    # Test with invalid span name
    with pytest.raises(TracingError):
        await tracing_manager.start_span("")
    
    # Test with invalid context
    with pytest.raises(TracingError):
        await tracing_manager.start_span(
            "test",
            context="invalid_context"
        )

@pytest.mark.asyncio
async def test_span_lifecycle(tracing_manager):
    """Test span lifecycle management"""
    start_time = datetime.now()
    
    # Create span
    span = await tracing_manager.start_span("test_operation")
    
    # Add some events and attributes
    await span.add_event("processing_started")
    await span.set_attribute("processor_id", "proc1")
    
    # End span
    await span.end()
    
    assert span.start_time >= start_time
    assert span.end_time > span.start_time
    assert span.duration > 0

@pytest.mark.asyncio
async def test_trace_metrics(tracing_manager):
    """Test tracing metrics collection"""
    metrics = []
    tracing_manager.set_metrics_callback(metrics.append)
    
    # Generate some spans
    for _ in range(5):
        span = await tracing_manager.start_span("test_operation")
        await span.end()
    
    assert len(metrics) > 0
    assert any(m["type"] == "span_created" for m in metrics)
    assert any(m["type"] == "span_ended" for m in metrics)

@pytest.mark.asyncio
async def test_batch_operations(tracing_manager):
    """Test batch span operations"""
    # Create multiple spans
    spans = []
    for i in range(10):
        span = await tracing_manager.start_span(f"operation_{i}")
        spans.append(span)
    
    # Batch end spans
    await tracing_manager.end_spans(spans)
    
    assert all(span.end_time is not None for span in spans)
    
    # Batch export
    exported = await tracing_manager.export_spans(spans)
    assert len(exported) == 10 