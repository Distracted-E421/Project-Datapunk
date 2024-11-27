"""
Distributed Tracing Infrastructure for Datapunk Service Mesh

Implements intelligent sampling and correlation for distributed tracing across
the service mesh. Provides context propagation and baggage handling for
end-to-end transaction tracking.

Key features:
- Adaptive sampling based on operation value
- Correlation ID propagation
- Error tracking with increased sampling
- Debug mode support
- Structured logging integration

Performance considerations:
- Uses context variables for thread safety
- Implements efficient sampling decisions
- Batches span exports for throughput

NOTE: This is a critical observability component. Changes should consider
impact on system-wide debugging capabilities and storage costs.
"""

from typing import Optional, Dict, Any, List
import structlog
from opentelemetry import trace, context
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.trace.span import Span
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.baggage import set_baggage, get_baggage
from functools import wraps
import contextvars
import random
import time

logger = structlog.get_logger()
current_span = contextvars.ContextVar("current_span", default=None)

class SamplingConfig:
    """
    Configuration for intelligent trace sampling.
    
    Implements different sampling rates based on operation characteristics:
    - base_rate: Default sampling probability
    - error_rate: Sampling rate for error cases
    - high_value_rate: Rate for important operations
    - debug_rate: Rate when debug mode is enabled
    
    NOTE: Rates should be tuned based on traffic volume and storage capacity.
    """
    def __init__(self,
                 base_rate: float = 1.0,
                 error_rate: float = 1.0,
                 high_value_rate: float = 1.0,
                 debug_rate: float = 1.0):
        self.base_rate = base_rate
        self.error_rate = error_rate
        self.high_value_rate = high_value_rate
        self.debug_rate = debug_rate

class CustomSampler(sampling.Sampler):
    """
    Intelligent sampling strategy for trace collection.
    
    Implements adaptive sampling based on:
    - Parent trace context
    - Error conditions
    - Operation value
    - Debug status
    
    TODO: Add rate limiting for high-cardinality traces
    FIXME: Improve sampling coordination across services
    """
    
    def __init__(self, config: SamplingConfig):
        self.config = config
        
    def should_sample(self, 
                     parent_context: Optional[context.Context],
                     trace_id: int,
                     name: str,
                     kind: SpanKind = None,
                     attributes: Dict = None,
                     links: List = None,
                     trace_state: Optional[Dict] = None) -> sampling.Decision:
        """
        Determine if span should be sampled based on context and configuration.
        
        Sampling logic prioritizes:
        1. Parent context (maintain trace continuity)
        2. Error cases (capture failure scenarios)
        3. High-value operations (business critical paths)
        4. Debug mode (development support)
        5. Base sampling rate (general visibility)
        """
        # Maintain trace continuity
        if parent_context and parent_context.trace_flags.sampled:
            return sampling.Decision.RECORD_AND_SAMPLE
            
        # Prioritize error cases
        if attributes and attributes.get("error", False):
            if random.random() < self.config.error_rate:
                return sampling.Decision.RECORD_AND_SAMPLE
                
        # Sample high-value operations
        if attributes and attributes.get("high_value", False):
            if random.random() < self.config.high_value_rate:
                return sampling.Decision.RECORD_AND_SAMPLE
                
        # Support debug mode
        if attributes and attributes.get("debug", False):
            if random.random() < self.config.debug_rate:
                return sampling.Decision.RECORD_AND_SAMPLE
                
        # Apply base sampling rate
        if random.random() < self.config.base_rate:
            return sampling.Decision.RECORD_AND_SAMPLE
            
        return sampling.Decision.DROP

class TracingConfig:
    """Configuration for tracing."""
    def __init__(self,
                 service_name: str,
                 jaeger_host: str = "jaeger",
                 jaeger_port: int = 6831,
                 sampling_config: Optional[SamplingConfig] = None):
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.sampling_config = sampling_config or SamplingConfig()

class TracingManager:
    """Manages distributed tracing."""
    
    def __init__(self, config: TracingConfig):
        self.config = config
        self.logger = logger.bind(component="tracing")
        
        # Initialize tracer with custom sampler
        resource = Resource.create({
            "service.name": config.service_name,
            "service.version": "1.0.0",  # TODO: Get from config
            "deployment.environment": "production"  # TODO: Get from config
        })
        
        provider = TracerProvider(
            resource=resource,
            sampler=CustomSampler(config.sampling_config)
        )
        trace.set_tracer_provider(provider)
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=config.jaeger_host,
            agent_port=config.jaeger_port,
        )
        
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        self.tracer = trace.get_tracer(__name__)
        
    def start_span(self,
                  name: str,
                  context: Optional[Dict] = None,
                  kind: Optional[str] = None,
                  attributes: Optional[Dict] = None) -> Span:
        """Start a new span with correlation context."""
        parent = current_span.get()
        
        # Create span
        span = self.tracer.start_span(
            name=name,
            context=context,
            kind=kind,
            attributes=attributes or {}
        )
        
        # Add correlation ID to baggage
        correlation_id = attributes.get("correlation_id") if attributes else None
        if correlation_id:
            set_baggage("correlation_id", correlation_id)
        
        current_span.set(span)
        return span
    
    def inject_context_to_log(self, log_event: Dict) -> Dict:
        """Inject tracing context into log event."""
        span = current_span.get()
        if span:
            log_event.update({
                "trace_id": format(span.get_span_context().trace_id, "032x"),
                "span_id": format(span.get_span_context().span_id, "016x"),
                "correlation_id": get_baggage("correlation_id")
            })
        return log_event
    
    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID."""
        return get_baggage("correlation_id")

def with_trace(name: Optional[str] = None,
               attributes: Optional[Dict] = None,
               high_value: bool = False):
    """Enhanced decorator for tracing methods."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get tracing manager from first arg (self) if available
            tracer = getattr(args[0], 'tracing', None) if args else None
            if not tracer:
                return await func(*args, **kwargs)
            
            span_name = name or func.__name__
            span_attributes = {
                **(attributes or {}),
                "high_value": high_value,
                "function": func.__name__,
                "module": func.__module__
            }
            
            with tracer.start_span(span_name, attributes=span_attributes) as span:
                try:
                    # Add function parameters as span attributes
                    span.set_attribute("args", str(args[1:]))  # Skip self
                    span.set_attribute("kwargs", str(kwargs))
                    
                    result = await func(*args, **kwargs)
                    
                    # Add result summary to span
                    span.set_attribute("result.success", True)
                    return result
                    
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR))
                    # Add error flag for sampling
                    span.set_attribute("error", True)
                    raise
                    
        return wrapper
    return decorator 