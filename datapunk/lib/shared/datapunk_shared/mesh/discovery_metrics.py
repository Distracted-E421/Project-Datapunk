from prometheus_client import Counter, Histogram, Gauge

class ServiceDiscoveryMetrics:
    """Metrics for service discovery operations."""
    
    def __init__(self, metrics_client):
        self.metrics = metrics_client
        
        # Counters
        self.registrations = Counter(
            'service_discovery_registrations_total',
            'Total number of service registrations',
            ['service']
        )
        
        self.discoveries = Counter(
            'service_discovery_lookups_total',
            'Total number of service discoveries',
            ['service', 'cached']
        )
        
        self.errors = Counter(
            'service_discovery_errors_total',
            'Total number of service discovery errors',
            ['service', 'operation', 'error_type']
        )
        
        # Histograms
        self.discovery_duration = Histogram(
            'service_discovery_duration_seconds',
            'Time spent discovering services',
            ['service', 'cached']
        )
        
        # Gauges
        self.healthy_instances = Gauge(
            'service_discovery_healthy_instances',
            'Number of healthy service instances',
            ['service']
        )
    
    def record_registration(self, service_name: str):
        """Record service registration."""
        self.registrations.labels(service=service_name).inc()
    
    def record_discovery(self,
                        service_name: str,
                        instance_count: int,
                        cached: bool = False):
        """Record service discovery operation."""
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
        """Record service discovery error."""
        self.errors.labels(
            service=service_name,
            operation=operation,
            error_type=error_type
        ).inc() 