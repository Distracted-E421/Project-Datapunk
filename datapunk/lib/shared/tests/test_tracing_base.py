import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode
from opentelemetry.trace.span import Span
from opentelemetry.sdk.trace import sampling
import random
from datapunk_shared.tracing import (
    SamplingConfig, CustomSampler, TracingConfig, TracingManager,
    with_trace, current_span
)

@pytest.fixture
def sampling_config():
    return SamplingConfig(
        base_rate=0.1,
        error_rate=1.0,
        high_value_rate=0.5,
        debug_rate=1.0
    )

@pytest.fixture
def tracing_config():
    return TracingConfig(
        service_name="test-service",
        jaeger_host="localhost",
        jaeger_port=6831,
        sampling_config=SamplingConfig()
    )

@pytest.fixture
def mock_span():
    span = MagicMock(spec=Span)
    context = MagicMock()
    context.trace_id = 123456
    context.span_id = 789012
    span.get_span_context.return_value = context
    return span

@pytest.fixture
def mock_tracer():
    tracer = MagicMock()
    tracer.start_span.return_value = mock_span()
    return tracer

@pytest.fixture
def tracing_manager(tracing_config):
    with patch('opentelemetry.trace.set_tracer_provider'), \
         patch('opentelemetry.exporter.jaeger.thrift.JaegerExporter'), \
         patch('opentelemetry.sdk.trace.TracerProvider'):
        manager = TracingManager(tracing_config)
        manager.tracer = mock_tracer()
        return manager

def test_sampling_config_initialization():
    """Test sampling configuration initialization"""
    config = SamplingConfig(
        base_rate=0.1,
        error_rate=1.0,
        high_value_rate=0.5,
        debug_rate=1.0
    )
    
    assert config.base_rate == 0.1
    assert config.error_rate == 1.0
    assert config.high_value_rate == 0.5
    assert config.debug_rate == 1.0

def test_custom_sampler_parent_context(sampling_config):
    """Test sampling decision with parent context"""
    sampler = CustomSampler(sampling_config)
    parent_context = MagicMock()
    parent_context.trace_flags.sampled = True
    
    decision = sampler.should_sample(
        parent_context=parent_context,
        trace_id=123,
        name="test_span"
    )
    
    assert decision == sampling.Decision.RECORD_AND_SAMPLE

def test_custom_sampler_error_case(sampling_config):
    """Test sampling decision for error cases"""
    sampler = CustomSampler(sampling_config)
    attributes = {"error": True}
    
    with patch('random.random', return_value=0.5):
        decision = sampler.should_sample(
            parent_context=None,
            trace_id=123,
            name="test_span",
            attributes=attributes
        )
        
        assert decision == sampling.Decision.RECORD_AND_SAMPLE

def test_custom_sampler_high_value(sampling_config):
    """Test sampling decision for high-value operations"""
    sampler = CustomSampler(sampling_config)
    attributes = {"high_value": True}
    
    with patch('random.random', return_value=0.3):
        decision = sampler.should_sample(
            parent_context=None,
            trace_id=123,
            name="test_span",
            attributes=attributes
        )
        
        assert decision == sampling.Decision.RECORD_AND_SAMPLE

def test_custom_sampler_debug_mode(sampling_config):
    """Test sampling decision in debug mode"""
    sampler = CustomSampler(sampling_config)
    attributes = {"debug": True}
    
    with patch('random.random', return_value=0.5):
        decision = sampler.should_sample(
            parent_context=None,
            trace_id=123,
            name="test_span",
            attributes=attributes
        )
        
        assert decision == sampling.Decision.RECORD_AND_SAMPLE

def test_tracing_manager_initialization(tracing_config):
    """Test tracing manager initialization"""
    with patch('opentelemetry.trace.set_tracer_provider') as mock_set_provider, \
         patch('opentelemetry.exporter.jaeger.thrift.JaegerExporter') as mock_exporter, \
         patch('opentelemetry.sdk.trace.TracerProvider') as mock_provider:
        
        TracingManager(tracing_config)
        
        mock_set_provider.assert_called_once()
        mock_exporter.assert_called_once_with(
            agent_host_name="localhost",
            agent_port=6831
        )
        mock_provider.assert_called_once()

def test_start_span(tracing_manager):
    """Test span creation and context management"""
    attributes = {
        "correlation_id": "test-123",
        "custom_attr": "value"
    }
    
    span = tracing_manager.start_span(
        name="test_operation",
        attributes=attributes
    )
    
    tracing_manager.tracer.start_span.assert_called_once_with(
        name="test_operation",
        context=None,
        kind=None,
        attributes=attributes
    )
    assert current_span.get() == span

def test_inject_context_to_log(tracing_manager, mock_span):
    """Test tracing context injection into log events"""
    current_span.set(mock_span)
    
    log_event = {"message": "test log"}
    enhanced_event = tracing_manager.inject_context_to_log(log_event)
    
    assert "trace_id" in enhanced_event
    assert "span_id" in enhanced_event
    assert enhanced_event["trace_id"] == format(123456, "032x")
    assert enhanced_event["span_id"] == format(789012, "016x")

@pytest.mark.asyncio
async def test_trace_decorator():
    """Test tracing decorator functionality"""
    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_tracer.start_span.return_value.__enter__.return_value = mock_span
    
    class TestService:
        def __init__(self):
            self.tracing = mock_tracer
        
        @with_trace(name="test_operation", attributes={"attr": "value"}, high_value=True)
        async def test_method(self, param1, param2="default"):
            return "result"
    
    service = TestService()
    result = await service.test_method("test", param2="custom")
    
    assert result == "result"
    mock_tracer.start_span.assert_called_once()
    mock_span.set_attribute.assert_any_call("high_value", True)
    mock_span.set_attribute.assert_any_call("function", "test_method")

@pytest.mark.asyncio
async def test_trace_decorator_error_handling():
    """Test error handling in tracing decorator"""
    mock_tracer = MagicMock()
    mock_span = MagicMock()
    mock_tracer.start_span.return_value.__enter__.return_value = mock_span
    
    class TestService:
        def __init__(self):
            self.tracing = mock_tracer
        
        @with_trace()
        async def failing_method(self):
            raise ValueError("Test error")
    
    service = TestService()
    with pytest.raises(ValueError):
        await service.failing_method()
    
    mock_span.record_exception.assert_called_once()
    mock_span.set_status.assert_called_once_with(Status(StatusCode.ERROR))
    mock_span.set_attribute.assert_any_call("error", True)

def test_correlation_id_propagation(tracing_manager):
    """Test correlation ID propagation through baggage"""
    attributes = {"correlation_id": "test-correlation-123"}
    
    tracing_manager.start_span("test_span", attributes=attributes)
    correlation_id = tracing_manager.get_correlation_id()
    
    assert correlation_id == "test-correlation-123"

def test_span_attributes(tracing_manager):
    """Test span attribute management"""
    attributes = {
        "service": "test-service",
        "operation": "test-operation",
        "custom": "value"
    }
    
    span = tracing_manager.start_span("test_span", attributes=attributes)
    
    tracing_manager.tracer.start_span.assert_called_once_with(
        name="test_span",
        context=None,
        kind=None,
        attributes=attributes
    )

@pytest.mark.asyncio
async def test_trace_decorator_without_tracing():
    """Test tracing decorator behavior when tracing is not available"""
    class TestService:
        @with_trace()
        async def test_method(self):
            return "result"
    
    service = TestService()
    result = await service.test_method()
    
    assert result == "result" 