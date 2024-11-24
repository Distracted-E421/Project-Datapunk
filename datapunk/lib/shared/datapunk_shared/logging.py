import structlog
from typing import Dict, Any
from .tracing import TracingManager

class TraceContextProcessor:
    """Processor that adds trace context to log events."""
    
    def __init__(self, tracing_manager: TracingManager):
        self.tracing = tracing_manager
    
    def __call__(self, logger: str, method_name: str, event_dict: Dict) -> Dict:
        """Add trace context to log event."""
        return self.tracing.inject_context_to_log(event_dict)

def configure_logging(service_name: str, tracing_manager: TracingManager):
    """Configure structured logging with trace correlation."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            TraceContextProcessor(tracing_manager),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True
    ) 