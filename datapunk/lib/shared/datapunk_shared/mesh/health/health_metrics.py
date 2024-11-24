from typing import Dict, Any, Optional
import structlog
from prometheus_client import Counter, Gauge, Histogram
from datetime import datetime

logger = structlog.get_logger()

class HealthMetrics:
    """Metrics collection for health checks."""
    
    def __init__(self):
        # Counters
        self.check_total = Counter(
            'health_check_total',
            'Total number of health checks performed',
            ['service', 'check_type']
        )
        
        self.check_failures = Counter(
            'health_check_failures_total',
            'Total number of health check failures',
            ['service', 'check_type', 'status']
        )
        
        # Gauges
        self.health_status = Gauge(
            'service_health_status',
            'Current health status (0=unhealthy, 1=degraded, 2=healthy)',
            ['service', 'check_type']
        )
        
        self.dependency_health = Gauge(
            'dependency_health_status',
            'Current health status of dependencies',
            ['service', 'dependency']
        )
        
        # Resource metrics
        self.resource_usage = Gauge(
            'resource_health_usage',
            'Resource usage metrics from health checks',
            ['service', 'resource_type']
        )
        
        # Histograms
        self.check_duration = Histogram(
            'health_check_duration_seconds',
            'Time spent performing health checks',
            ['service', 'check_type']
        )
        
        self.dependency_latency = Histogram(
            'dependency_latency_seconds',
            'Latency to dependencies',
            ['service', 'dependency']
        )
    
    def record_check(self,
                    service: str,
                    check_type: str,
                    status: str,
                    duration: float,
                    details: Dict[str, Any] = None):
        """Record health check execution."""
        # Update counters
        self.check_total.labels(
            service=service,
            check_type=check_type
        ).inc()
        
        if status != "healthy":
            self.check_failures.labels(
                service=service,
                check_type=check_type,
                status=status
            ).inc()
        
        # Update status gauge
        status_value = {
            "healthy": 2,
            "degraded": 1,
            "unhealthy": 0
        }.get(status, 0)
        
        self.health_status.labels(
            service=service,
            check_type=check_type
        ).set(status_value)
        
        # Record check duration
        self.check_duration.labels(
            service=service,
            check_type=check_type
        ).observe(duration)
        
        # Record resource metrics if available
        if details and "resources" in details:
            for resource, value in details["resources"].items():
                self.resource_usage.labels(
                    service=service,
                    resource_type=resource
                ).set(value)
    
    def record_dependency_health(self,
                               service: str,
                               dependency: str,
                               healthy: bool,
                               latency: Optional[float] = None):
        """Record dependency health status."""
        self.dependency_health.labels(
            service=service,
            dependency=dependency
        ).set(1 if healthy else 0)
        
        if latency is not None:
            self.dependency_latency.labels(
                service=service,
                dependency=dependency
            ).observe(latency)
    
    def clear_service_metrics(self, service: str):
        """Clear all metrics for a service."""
        # Remove service-specific metrics when service is deregistered
        self.health_status.remove(service)
        self.dependency_health.remove(service)
        self.resource_usage.remove(service) 