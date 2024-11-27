from prometheus_client import Counter, Histogram, Gauge

"""
Service discovery metrics collection for monitoring and debugging.

Provides comprehensive metrics for:
- Service registration events
- Discovery operations and performance
- Error patterns and frequencies
- Instance health status
- Cache effectiveness

NOTE: Uses Prometheus-style metrics for compatibility
"""

class ServiceDiscoveryMetrics:
    """
    Metrics collector for service discovery operations.
    
    Tracks key indicators:
    - Registration success/failure rates
    - Discovery latency patterns
    - Error distributions
    - Instance health states
    - Cache hit ratios
    
    TODO: Add service dependency mapping
    """
    
    def __init__(self, metrics_client):
        """
        Initialize metric collectors with appropriate labels.
        
        Metrics are organized by:
        - Operation type (registration, discovery)
        - Performance indicators (duration, success rate)
        - Health status (instance counts)
        
        NOTE: Labels allow for detailed analysis and alerting
        """
        self.metrics = metrics_client
        
        # Track service registration events
        # Labels: service name for granular monitoring
        self.registrations = Counter(
            'service_discovery_registrations_total',
            'Total number of service registrations',
            ['service']
        )
        
        # Monitor discovery operations
        # Labels: service name and cache status for performance analysis
        self.discoveries = Counter(
            'service_discovery_lookups_total',
            'Total number of service discoveries',
            ['service', 'cached']
        )
        
        # Track error patterns
        # Labels: service, operation, and error type for troubleshooting
        self.errors = Counter(
            'service_discovery_errors_total',
            'Total number of service discovery errors',
            ['service', 'operation', 'error_type']
        )
        
        # Measure operation latency
        # Labels: service and cache status for performance optimization
        self.discovery_duration = Histogram(
            'service_discovery_duration_seconds',
            'Time spent discovering services',
            ['service', 'cached']
        )
        
        # Monitor service health
        # Labels: service name for availability tracking
        self.healthy_instances = Gauge(
            'service_discovery_healthy_instances',
            'Number of healthy service instances',
            ['service']
        )
    
    def record_registration(self, service_name: str):
        """
        Record service registration attempt.
        
        Used for:
        - Registration pattern analysis
        - Service lifecycle monitoring
        - Deployment tracking
        """
        self.registrations.labels(service=service_name).inc()
    
    def record_discovery(self,
                        service_name: str,
                        instance_count: int,
                        cached: bool = False):
        """
        Record service discovery operation with cache status.
        
        Tracks:
        - Discovery frequency
        - Cache effectiveness
        - Instance availability
        
        NOTE: Instance count helps detect service scaling
        """
        self.discoveries.labels(
            service=service_name,
            cached=str(cached).lower()
        ).inc()
        
        self.healthy_instances.labels(
            service=service_name
        ).set(instance_count)
    
    def record_error(self,
                    service_name: str,
                    operation: str,
                    error_type: str):
        """
        Record service discovery errors with categorization.
        
        Categories:
        - Network failures
        - Timeout errors
        - Configuration issues
        - Authorization failures
        
        Used for:
        - Error pattern detection
        - SLO monitoring
        - Troubleshooting
        """
        self.errors.labels(
            service=service_name,
            operation=operation,
            error_type=error_type
        ).inc() 