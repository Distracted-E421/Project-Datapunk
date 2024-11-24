from typing import Optional, Dict, Any
import structlog
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.span import Span
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from functools import wraps
import contextvars

logger = structlog.get_logger()
current_span = contextvars.ContextVar("current_span", default=None)

class TracingConfig:
    """Configuration for tracing."""
    def __init__(self,
                 service_name: str,
                 jaeger_host: str = "jaeger",
                 jaeger_port: int = 6831,
                 sample_rate: float = 1.0):
        self.service_name = service_name
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.sample_rate = sample_rate

class TracingManager:
    """Manages distributed tracing."""
    
    def __init__(self, config: TracingConfig):
        self.config = config
        self.logger = logger.bind(component="tracing")
        
        # Initialize tracer
        resource = Resource.create({"service.name": config.service_name})
        trace.set_tracer_provider(TracerProvider(resource=resource))
        
        # Configure Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=config.jaeger_host,
            agent_port=config.jaeger_port,
        )
        
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
        
        self.tracer = trace.get_tracer(__name__)
    
    def start_span(self,
                  name: str,
                  context: Optional[Dict] = None,
                  kind: Optional[str] = None) -> Span:
        """Start a new span."""
        parent = current_span.get()
        
        span = self.tracer.start_span(
            name=name,
            context=context,
            kind=kind,
            parent=parent
        )
        
        current_span.set(span)
        return span
    
    def end_span(self, span: Span, status: Optional[Status] = None):
        """End a span with optional status."""
        if status:
            span.set_status(status)
        span.end()
        current_span.set(None)
    
    def add_event(self, name: str, attributes: Optional[Dict] = None):
        """Add event to current span."""
        span = current_span.get()
        if span:
            span.add_event(name, attributes=attributes)
    
    def set_attribute(self, key: str, value: Any):
        """Set attribute on current span."""
        span = current_span.get()
        if span:
            span.set_attribute(key, value)
    
    def record_exception(self, exception: Exception):
        """Record exception in current span."""
        span = current_span.get()
        if span:
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR))

def trace_method(name: Optional[str] = None):
    """Decorator for tracing methods."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get tracing manager from first arg (self) if available
            tracer = getattr(args[0], 'tracing', None) if args else None
            if not tracer:
                return await func(*args, **kwargs)
            
            span_name = name or func.__name__
            with tracer.start_span(span_name) as span:
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
                    raise
                    
        return wrapper
    return decorator 