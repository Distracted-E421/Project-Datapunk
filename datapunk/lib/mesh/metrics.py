from typing import Dict
from dataclasses import dataclass, field
import time
import structlog
from prometheus_client import Counter, Histogram, Gauge

logger = structlog.get_logger()

"""
Comprehensive metrics collection for service mesh components.

Provides monitoring for:
- Load balancer performance
- Retry operations
- Service health
- Error patterns
- Latency tracking

NOTE: Uses Prometheus-style metrics for compatibility
"""

@dataclass
class LoadBalancerMetrics:
    """
    Load balancer performance and health metrics.
    
    Tracks:
    - Request distribution
    - Error patterns
    - Latency profiles
    - Connection states
    - Instance health
    
    TODO: Add predictive load indicators
    """
    
    # Counters
    requests_total: Counter = field(default_factory=lambda: Counter(
        'load_balancer_requests_total',
        'Total number of requests handled by load balancer',
        ['service', 'instance', 'strategy']
    ))
    
    errors_total: Counter = field(default_factory=lambda: Counter(
        'load_balancer_errors_total',
        'Total number of load balancing errors',
        ['service', 'error_type']
    ))
    
    # Histograms
    request_duration_seconds: Histogram = field(default_factory=lambda: Histogram(
        'load_balancer_request_duration_seconds',
        'Request duration in seconds',
        ['service', 'instance']
    ))
    
    # Gauges
    active_connections: Gauge = field(default_factory=lambda: Gauge(
        'load_balancer_active_connections',
        'Number of active connections per instance',
        ['service', 'instance']
    ))
    
    instance_health_score: Gauge = field(default_factory=lambda: Gauge(
        'load_balancer_instance_health_score',
        'Health score of each instance',
        ['service', 'instance']
    ))

    def record_request(self, service: str, instance: str, strategy: str):
        """
        Record load balancing decision.
        
        Used for:
        - Strategy effectiveness analysis
        - Load distribution patterns
        - Instance utilization tracking
        
        NOTE: Labels enable detailed analysis
        """
        self.requests_total.labels(
            service=service,
            instance=instance,
            strategy=strategy
        ).inc()

    def record_error(self, service: str, error_type: str):
        """Record a load balancing error."""
        self.errors_total.labels(
            service=service,
            error_type=error_type
        ).inc()

    def observe_request_duration(self, service: str, instance: str, duration: float):
        """Record the duration of a request."""
        self.request_duration_seconds.labels(
            service=service,
            instance=instance
        ).observe(duration)

    def update_active_connections(self, service: str, instance: str, connections: int):
        """Update the number of active connections."""
        self.active_connections.labels(
            service=service,
            instance=instance
        ).set(connections)

    def update_health_score(self, service: str, instance: str, score: float):
        """
        Update instance health score.
        
        Score factors:
        - Response latency
        - Error rates
        - Connection states
        - Custom health checks
        
        WARNING: Score changes affect routing decisions
        """
        self.instance_health_score.labels(
            service=service,
            instance=instance
        ).set(score) 

@dataclass
class RetryMetrics:
    """
    Retry operation performance tracking.
    
    Monitors:
    - Retry patterns
    - Success rates
    - Error categories
    - Operation duration
    
    NOTE: Helps tune retry policies
    """
    
    retry_attempts_total: Counter = field(default_factory=lambda: Counter(
        'retry_attempts_total',
        'Total number of retry attempts',
        ['service', 'operation', 'attempt']
    ))
    
    retry_success_total: Counter = field(default_factory=lambda: Counter(
        'retry_success_total',
        'Total number of successful retries',
        ['service', 'operation', 'attempts_needed']
    ))
    
    retry_failure_total: Counter = field(default_factory=lambda: Counter(
        'retry_failure_total',
        'Total number of failed retries',
        ['service', 'operation', 'error_type']
    ))
    
    retry_duration_seconds: Histogram = field(default_factory=lambda: Histogram(
        'retry_duration_seconds',
        'Duration of retry operations',
        ['service', 'operation']
    ))

    def record_attempt(self, service: str, operation: str, attempt: int):
        """Record a retry attempt."""
        self.retry_attempts_total.labels(
            service=service,
            operation=operation,
            attempt=attempt
        ).inc()

    def record_success(self, service: str, operation: str, attempts: int, duration: float):
        """
        Record successful retry operation.
        
        Captures:
        - Attempt count impact
        - Duration patterns
        - Service behavior
        
        Used for retry policy optimization
        """
        self.retry_success_total.labels(
            service=service,
            operation=operation,
            attempts_needed=attempts
        ).inc()
        
        self.retry_duration_seconds.labels(
            service=service,
            operation=operation
        ).observe(duration)

    def record_failure(self, service: str, operation: str, attempts: int, error: str):
        """Record a failed retry operation."""
        self.retry_failure_total.labels(
            service=service,
            operation=operation,
            error_type=error
        ).inc() 

@dataclass
class ServiceMeshMetrics:
    """
    Combined service mesh performance metrics.
    
    Provides:
    - Registration tracking
    - Call monitoring
    - Health status
    - Circuit breaker states
    
    WARNING: High cardinality metrics may impact performance
    TODO: Add metric aggregation support
    """
    
    # Service registration metrics
    registrations_total: Counter = field(default_factory=lambda: Counter(
        'mesh_service_registrations_total',
        'Total number of service registrations',
        ['service']
    ))
    
    registration_failures_total: Counter = field(default_factory=lambda: Counter(
        'mesh_registration_failures_total',
        'Total number of failed registrations',
        ['service', 'error_type']
    ))
    
    # Service call metrics
    calls_total: Counter = field(default_factory=lambda: Counter(
        'mesh_service_calls_total',
        'Total number of service calls',
        ['service', 'operation', 'status']
    ))
    
    call_duration_seconds: Histogram = field(default_factory=lambda: Histogram(
        'mesh_call_duration_seconds',
        'Service call duration in seconds',
        ['service', 'operation']
    ))
    
    # Health metrics
    healthy_instances: Gauge = field(default_factory=lambda: Gauge(
        'mesh_healthy_instances',
        'Number of healthy service instances',
        ['service']
    ))
    
    circuit_breaker_state: Gauge = field(default_factory=lambda: Gauge(
        'mesh_circuit_breaker_state',
        'Circuit breaker state (0=open, 1=half-open, 2=closed)',
        ['service']
    ))
    
    def record_registration(self, service: str):
        """Record service registration."""
        self.registrations_total.labels(service=service).inc()
    
    def record_registration_failure(self, service: str, error: str):
        """Record registration failure."""
        self.registration_failures_total.labels(
            service=service,
            error_type=error
        ).inc()
    
    def record_call_success(self,
                           service: str,
                           operation: str,
                           duration: float):
        """
        Record successful service call.
        
        Tracks:
        - Operation latency
        - Service reliability
        - Usage patterns
        
        Used for:
        - Performance monitoring
        - Capacity planning
        - SLO tracking
        """
        self.calls_total.labels(
            service=service,
            operation=operation,
            status="success"
        ).inc()
        
        self.call_duration_seconds.labels(
            service=service,
            operation=operation
        ).observe(duration)
    
    def record_call_failure(self,
                           service: str,
                           operation: str,
                           error: str):
        """
        Record failed service call.
        
        Categorizes:
        - Error types
        - Failure patterns
        - Service issues
        
        NOTE: Error categorization aids troubleshooting
        """
        self.calls_total.labels(
            service=service,
            operation=operation,
            status="failure"
        ).inc() 