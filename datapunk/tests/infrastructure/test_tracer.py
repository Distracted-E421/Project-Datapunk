import pytest
import asyncio
import json
from datetime import datetime, timedelta
from src.infrastructure.tracer import (
    SpanKind, SpanContext, Span, Sampler,
    SpanProcessor, Tracer, AsyncTracer
)

@pytest.fixture
def sampler():
    return Sampler(sample_rate=1.0)

@pytest.fixture
def processor():
    return SpanProcessor()

@pytest.fixture
def tracer(sampler):
    return Tracer(sampler)

@pytest.fixture
def async_tracer(sampler):
    return AsyncTracer(sampler)

def test_sampler():
    # Test 100% sampling
    sampler = Sampler(1.0)
    assert sampler.should_sample("1234567890abcdef") is True
    
    # Test 0% sampling
    sampler = Sampler(0.0)
    assert sampler.should_sample("1234567890abcdef") is False
    
    # Test invalid rates
    with pytest.raises(ValueError):
        Sampler(-0.1)
    with pytest.raises(ValueError):
        Sampler(1.1)

def test_span_processor(processor):
    # Create a test span
    context = SpanContext(
        trace_id="trace1",
        span_id="span1"
    )
    span = Span(
        name="test_span",
        context=context,
        kind=SpanKind.INTERNAL,
        start_time=datetime.now()
    )
    
    # Test span processing
    processor.on_start(span)
    span.end_time = datetime.now()
    processor.on_end(span)
    
    # Test trace retrieval
    spans = processor.get_trace("trace1")
    assert len(spans) == 1
    assert spans[0].name == "test_span"
    
    # Test trace export
    exported = processor.export_trace("trace1")
    data = json.loads(exported)
    assert data["trace_id"] == "trace1"
    assert len(data["spans"]) == 1
    assert data["spans"][0]["name"] == "test_span"
    
    # Test empty trace export
    assert processor.export_trace("nonexistent") == "{}"

def test_tracer_basic(tracer):
    # Test span creation
    with tracer.span("test_operation") as span:
        assert span.name == "test_operation"
        assert span.kind == SpanKind.INTERNAL
        assert span.start_time is not None
        assert span.end_time is None
    
    assert span.end_time is not None

def test_tracer_nested_spans(tracer):
    with tracer.span("parent") as parent:
        with tracer.span("child") as child:
            assert child.context.parent_span_id == parent.context.span_id
            assert child.context.trace_id == parent.context.trace_id

def test_tracer_attributes(tracer):
    attributes = {"key": "value"}
    with tracer.span("test", attributes=attributes) as span:
        assert span.attributes == attributes

def test_tracer_events(tracer):
    with tracer.span("test") as span:
        tracer.add_event(span, "event1", {"detail": "value"})
        tracer.add_event(span, "event2")
    
    assert len(span.events) == 2
    assert span.events[0]["name"] == "event1"
    assert span.events[0]["attributes"] == {"detail": "value"}
    assert span.events[1]["name"] == "event2"
    assert span.events[1]["attributes"] == {}

def test_tracer_status(tracer):
    with tracer.span("test") as span:
        tracer.set_status(span, "error", "Something went wrong")
    
    assert span.status_code == "error"
    assert span.status_message == "Something went wrong"

def test_tracer_export(tracer):
    with tracer.span("operation1"):
        with tracer.span("operation2"):
            pass
    
    # Get the trace ID from the first span
    trace_id = tracer.processor.spans.keys().__iter__().__next__()
    
    # Export the trace
    exported = tracer.export_trace(trace_id)
    data = json.loads(exported)
    
    assert len(data["spans"]) == 2
    assert data["spans"][0]["name"] == "operation1"
    assert data["spans"][1]["name"] == "operation2"
    assert data["spans"][1]["parent_span_id"] == data["spans"][0]["span_id"]

@pytest.mark.asyncio
async def test_async_tracer_basic(async_tracer):
    async with async_tracer.span("async_operation") as span:
        assert span.name == "async_operation"
        assert span.kind == SpanKind.INTERNAL
        assert span.start_time is not None
        assert span.end_time is None
    
    assert span.end_time is not None

@pytest.mark.asyncio
async def test_async_tracer_nested_spans(async_tracer):
    async with async_tracer.span("parent") as parent:
        async with async_tracer.span("child") as child:
            assert child.context.parent_span_id == parent.context.span_id
            assert child.context.trace_id == parent.context.trace_id

@pytest.mark.asyncio
async def test_async_tracer_concurrent_tasks(async_tracer):
    async def task1():
        async with async_tracer.span("task1"):
            await asyncio.sleep(0.1)
    
    async def task2():
        async with async_tracer.span("task2"):
            await asyncio.sleep(0.1)
    
    # Run tasks concurrently
    await asyncio.gather(task1(), task2())
    
    # Verify spans were created correctly
    all_spans = []
    for spans in async_tracer.processor.spans.values():
        all_spans.extend(spans)
    
    assert len(all_spans) == 2
    assert {span.name for span in all_spans} == {"task1", "task2"}

@pytest.mark.asyncio
async def test_async_tracer_task_isolation(async_tracer):
    results = []
    
    async def nested_spans():
        async with async_tracer.span("outer"):
            results.append(async_tracer.get_current_span().span_id)
            async with async_tracer.span("inner"):
                results.append(async_tracer.get_current_span().span_id)
    
    # Run multiple instances of the same task
    await asyncio.gather(
        nested_spans(),
        nested_spans()
    )
    
    # Verify each task had its own context
    assert len(results) == 4
    assert results[0] != results[2]  # Different outer spans
    assert results[1] != results[3]  # Different inner spans

@pytest.mark.asyncio
async def test_async_tracer_cleanup(async_tracer):
    async def task():
        async with async_tracer.span("test"):
            pass
    
    await task()
    
    # Verify task local storage was cleaned up
    assert len(async_tracer._task_local) == 0

def test_tracer_sampling(sampler, processor):
    # Test with 0% sampling
    no_sample_tracer = Tracer(Sampler(0.0))
    with no_sample_tracer.span("test") as span:
        assert span.context.sampled is False
    
    # Verify no spans were processed
    assert len(no_sample_tracer.processor.spans) == 0
    
    # Test with 100% sampling
    full_sample_tracer = Tracer(Sampler(1.0))
    with full_sample_tracer.span("test") as span:
        assert span.context.sampled is True
    
    # Verify spans were processed
    assert len(full_sample_tracer.processor.spans) == 1 