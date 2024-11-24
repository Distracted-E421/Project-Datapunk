"""
Error handling and reporting system.

This module provides a comprehensive error handling system with:
- Fine-grained error severity levels
- Detailed error categorization
- Structured error reporting
- Metrics integration
- Audit logging
- Alert management

Integration Points:
- Metrics: Error counts, categories, severities
- Messaging: Error events, alerts
- Audit: Compliance tracking, error history
- Monitoring: Health status updates

Usage:
    error_handler = ErrorHandler(reporter, severity=ErrorSeverity.ERROR)
    
    @with_error_handling(category=ErrorCategory.VALIDATION)
    async def my_function():
        ...

    # Or manually:
    try:
        result = await operation()
    except Exception as e:
        await error_handler.handle_error(
            error=e,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.HIGH
        )
"""

from typing import Dict, Optional, Any, TYPE_CHECKING, List, Set
import structlog
from datetime import datetime
import traceback
from enum import Enum
import json
from dataclasses import dataclass

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....messaging import MessageBroker

logger = structlog.get_logger()

class ErrorSeverity(Enum):
    """
    Error severity levels.
    
    Levels:
    - CRITICAL: System-wide impact, immediate action required
    - HIGH: Service disruption, urgent action needed
    - MEDIUM: Degraded functionality, action needed soon
    - LOW: Minor issue, action can be delayed
    - WARNING: Potential issue, monitoring needed
    - INFO: Informational, no action needed
    - DEBUG: Development/troubleshooting only
    """
    CRITICAL = "critical"  # System failure, data loss risk
    HIGH = "high"         # Service disruption
    MEDIUM = "medium"     # Degraded functionality
    LOW = "low"          # Minor issues
    WARNING = "warning"   # Potential issues
    INFO = "info"        # Informational
    DEBUG = "debug"      # Development only

class ErrorCategory(Enum):
    """
    Error categorization for tracking and analysis.
    
    Categories:
    - VALIDATION: Input/data validation failures
    - AUTHENTICATION: Auth-related failures
    - AUTHORIZATION: Permission/access failures
    - CONFIGURATION: Config/setup issues
    - INTEGRATION: External service issues
    - INFRASTRUCTURE: System/platform issues
    - BUSINESS_LOGIC: Application logic errors
    - DATA_ACCESS: Database/storage issues
    - SECURITY: Security-related issues
    - PERFORMANCE: Performance/timeout issues
    - COMPLIANCE: Compliance violations
    - RESOURCE: Resource exhaustion
    """
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    INTEGRATION = "integration"
    INFRASTRUCTURE = "infrastructure"
    BUSINESS_LOGIC = "business_logic"
    DATA_ACCESS = "data_access"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    RESOURCE = "resource"

@dataclass
class ErrorContext:
    """Structured context for error reporting."""
    timestamp: datetime
    service: str
    component: str
    operation: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    environment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ErrorThresholds:
    """Thresholds for error rate monitoring."""
    error_count: int = 100          # Errors per interval
    error_rate: float = 0.05        # Error rate threshold
    interval_seconds: int = 300     # Monitoring interval
    severity_multipliers: Dict[ErrorSeverity, float] = None  # Severity-based adjustments

class ErrorReporter:
    """
    Handles error reporting and tracking.
    
    Features:
    - Structured error logging
    - Metrics collection
    - Alert generation
    - Health status updates
    - Error rate monitoring
    - Severity-based handling
    """
    
    def __init__(self,
                 metrics: 'MetricsClient',
                 message_broker: 'MessageBroker',
                 service_name: str = "auth",
                 thresholds: Optional[ErrorThresholds] = None):
        self.metrics = metrics
        self.broker = message_broker
        self.service_name = service_name
        self.thresholds = thresholds or ErrorThresholds()
        self.logger = logger.bind(component="error_reporter")
    
    async def report_error(self,
                          error: Exception,
                          severity: ErrorSeverity,
                          category: ErrorCategory,
                          context: Optional[Dict[str, Any]] = None) -> str:
        """
        Report an error with full context.
        
        Args:
            error: The exception to report
            severity: Error severity level
            category: Error category
            context: Additional context data
        
        Returns:
            str: Unique error ID
        
        Raises:
            Exception: If reporting fails
        """
        try:
            error_id = f"err_{datetime.utcnow().timestamp()}"
            
            # Build error data
            error_data = {
                "error_id": error_id,
                "timestamp": datetime.utcnow().isoformat(),
                "service": self.service_name,
                "severity": severity.value,
                "category": category.value,
                "error_type": error.__class__.__name__,
                "error_message": str(error),
                "stacktrace": traceback.format_exc(),
                "context": context or {}
            }
            
            # Add error details
            if hasattr(error, "details"):
                error_data["details"] = error.details
            
            # Log error
            self._log_error(error_data)
            
            # Update metrics
            self._update_metrics(error_data)
            
            # Publish error event
            await self._publish_error_event(error_data)
            
            # Handle critical errors
            if severity == ErrorSeverity.CRITICAL:
                await self._handle_critical_error(error_data)
            
            # Check error thresholds
            await self._check_error_thresholds(error_data)
            
            return error_id
            
        except Exception as e:
            self.logger.error("error_reporting_failed",
                            error=str(e))
            return None
    
    def _log_error(self, error_data: Dict) -> None:
        """Log error with appropriate level and context."""
        log_method = {
            ErrorSeverity.CRITICAL: self.logger.critical,
            ErrorSeverity.HIGH: self.logger.error,
            ErrorSeverity.MEDIUM: self.logger.warning,
            ErrorSeverity.LOW: self.logger.info,
            ErrorSeverity.WARNING: self.logger.warning,
            ErrorSeverity.INFO: self.logger.info,
            ErrorSeverity.DEBUG: self.logger.debug
        }.get(ErrorSeverity(error_data["severity"]), self.logger.error)
        
        log_method("error_occurred",
                  error_id=error_data["error_id"],
                  severity=error_data["severity"],
                  category=error_data["category"],
                  error=error_data["error_message"],
                  context=error_data["context"])
    
    def _update_metrics(self, error_data: Dict) -> None:
        """Update error metrics."""
        labels = {
            "severity": error_data["severity"],
            "category": error_data["category"],
            "error_type": error_data["error_type"]
        }
        
        self.metrics.increment("errors_total", labels)
        self.metrics.gauge("error_severity", 
                         ErrorSeverity[error_data["severity"]].value,
                         labels)
    
    async def _publish_error_event(self, error_data: Dict) -> None:
        """Publish error event to message broker."""
        await self.broker.publish(
            f"errors.{error_data['severity']}",
            error_data
        )
    
    async def _handle_critical_error(self, error_data: Dict) -> None:
        """Handle critical errors with immediate actions."""
        # Send immediate alerts
        await self.broker.publish(
            "alerts.critical",
            {
                "type": "critical_error",
                "error_data": error_data,
                "requires_immediate_action": True,
                "alert_priority": "p1"
            }
        )
        
        # Update health status
        await self._update_health_status(error_data)
        
        # Trigger incident response if configured
        await self._trigger_incident_response(error_data)
    
    async def _check_error_thresholds(self, error_data: Dict) -> None:
        """Monitor error rates against thresholds."""
        # Implementation would track error rates and trigger alerts
        # This is a placeholder
        pass
    
    async def _trigger_incident_response(self, error_data: Dict) -> None:
        """Trigger automated incident response."""
        # Implementation would integrate with incident management
        # This is a placeholder
        pass

class ErrorHandler:
    """Utility for standardized error handling."""
    
    def __init__(self,
                 reporter: ErrorReporter,
                 default_severity: ErrorSeverity = ErrorSeverity.ERROR):
        self.reporter = reporter
        self.default_severity = default_severity
        self.logger = logger.bind(component="error_handler")
    
    async def handle_error(self,
                          error: Exception,
                          category: ErrorCategory,
                          severity: Optional[ErrorSeverity] = None,
                          context: Optional[Dict] = None,
                          should_raise: bool = True) -> Dict[str, Any]:
        """Handle an error with standard processing."""
        try:
            severity = severity or self.default_severity
            
            # Report error
            error_id = await self.reporter.report_error(
                error=error,
                severity=severity,
                category=category,
                context=context
            )
            
            # Build error response
            error_response = {
                "success": False,
                "error": {
                    "id": error_id,
                    "type": error.__class__.__name__,
                    "message": str(error),
                    "category": category.value,
                    "severity": severity.value
                }
            }
            
            if context:
                error_response["error"]["context"] = context
            
            # Raise if requested
            if should_raise:
                raise error
            
            return error_response
            
        except Exception as e:
            self.logger.error("error_handling_failed",
                            error=str(e))
            raise

def with_error_handling(category: ErrorCategory,
                       severity: Optional[ErrorSeverity] = None):
    """Decorator for automatic error handling."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get error handler from first arg (self) if available
                handler = getattr(args[0], "error_handler", None)
                if handler:
                    return await handler.handle_error(
                        error=e,
                        category=category,
                        severity=severity
                    )
                raise
        return wrapper
    return decorator 