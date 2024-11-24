from typing import Dict
import structlog
from prometheus_client import Counter, Gauge, Histogram

logger = structlog.get_logger()

class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    
    def __init__(self):
        # State tracking
        self.state = Gauge(
            'circuit_breaker_state',
            'Current circuit breaker state (0=open, 1=half-open, 2=closed)',
            ['service']
        )
        
        # Request tracking
        self.requests_total = Counter(
            'circuit_breaker_requests_total',
            'Total number of requests through circuit breaker',
            ['service', 'status']
        )
        
        self.rejections_total = Counter(
            'circuit_breaker_rejections_total',
            'Total number of rejected requests due to open circuit',
            ['service']
        )
        
        # Failure tracking
        self.failures_total = Counter(
            'circuit_breaker_failures_total',
            'Total number of failed requests',
            ['service', 'error_type']
        )
        
        # Timing metrics
        self.request_duration = Histogram(
            'circuit_breaker_request_duration_seconds',
            'Request duration through circuit breaker',
            ['service', 'status']
        )
        
        # State changes
        self.state_changes_total = Counter(
            'circuit_breaker_state_changes_total',
            'Total number of circuit breaker state changes',
            ['service', 'from_state', 'to_state']
        )
        
        # Health metrics
        self.error_rate = Gauge(
            'circuit_breaker_error_rate',
            'Current error rate for service',
            ['service']
        )
        
        self.recovery_time = Histogram(
            'circuit_breaker_recovery_time_seconds',
            'Time taken to recover from open state',
            ['service']
        )
    
    def record_request(self, service: str, status: str, duration: float):
        """Record request metrics."""
        self.requests_total.labels(
            service=service,
            status=status
        ).inc()
        
        self.request_duration.labels(
            service=service,
            status=status
        ).observe(duration)
    
    def record_success(self, service: str, duration: float):
        """Record successful request."""
        self.record_request(service, "success", duration)
    
    def record_failure(self, service: str, error_type: str, duration: float):
        """Record failed request."""
        self.record_request(service, "failure", duration)
        self.failures_total.labels(
            service=service,
            error_type=error_type
        ).inc()
    
    def record_rejection(self, service: str):
        """Record request rejection."""
        self.rejections_total.labels(service=service).inc()
    
    def record_state_change(self, service: str, new_state: str):
        """Record state change."""
        state_value = {
            "open": 0,
            "half-open": 1,
            "closed": 2
        }.get(new_state, 0)
        
        self.state.labels(service=service).set(state_value)
    
    def record_error_rate(self, service: str, rate: float):
        """Record current error rate."""
        self.error_rate.labels(service=service).set(rate)
    
    def record_recovery(self, service: str, duration: float):
        """Record recovery time."""
        self.recovery_time.labels(service=service).observe(duration) 