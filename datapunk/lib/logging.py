"""Structured logging configuration with distributed tracing integration.

This module implements the logging component of the observability stack defined
in sys-arch.mmd. It provides structured JSON logging with automatic trace
correlation, enabling end-to-end request tracking across the service mesh.

Key Features:
- Structured JSON log format
- Automatic trace context injection
- ISO timestamp formatting
- Stack trace formatting
- Log level filtering

Implementation Notes:
- Uses structlog for consistent JSON formatting
- Integrates with OpenTelemetry for distributed tracing
- Designed for ELK/Loki stack ingestion
- Maintains context across async boundaries
"""

import structlog
from typing import Dict, Any
from .tracing import TracingManager

class TraceContextProcessor:
    """Processor that enriches log events with distributed tracing context.
    
    Implements trace correlation by injecting OpenTelemetry trace context
    into log events, enabling end-to-end request tracking across services.
    
    Note: Must be added to structlog processors before JSONRenderer
    TODO: Add sampling configuration for high-volume services
    """
    
    def __init__(self, tracing_manager: TracingManager):
        """Initialize with tracing manager instance.
        
        Args:
            tracing_manager: Service's tracing manager instance
        """
        self.tracing = tracing_manager
    
    def __call__(self, logger: str, method_name: str, event_dict: Dict) -> Dict:
        """Add trace context to structured log event.
        
        Enriches log events with:
        - Trace ID
        - Span ID
        - Parent Span ID
        - Sampling flags
        
        Args:
            logger: Logger name
            method_name: Logging method called
            event_dict: Current log event dictionary
        
        Returns:
            Enhanced log event with trace context
        """
        return self.tracing.inject_context_to_log(event_dict)

def configure_logging(service_name: str, tracing_manager: TracingManager):
    """Configure service-wide structured logging with trace correlation.
    
    Sets up logging pipeline optimized for observability:
    1. ISO timestamp formatting for consistent parsing
    2. Log level annotation for filtering
    3. Stack trace formatting for error analysis
    4. Trace context injection for request tracking
    5. JSON rendering for log aggregation
    
    Args:
        service_name: Unique service identifier
        tracing_manager: Service's tracing manager instance
    
    Note: Configuration is immutable after first logger creation
    TODO: Add log sampling configuration for production
    """
    structlog.configure(
        processors=[
            # Time formatting for log aggregation
            structlog.processors.TimeStamper(fmt="iso"),
            # Add log level for filtering
            structlog.stdlib.add_log_level,
            # Format stack traces for error tracking
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Inject trace context for request tracking
            TraceContextProcessor(tracing_manager),
            # Render as JSON for log aggregation
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True
    ) 