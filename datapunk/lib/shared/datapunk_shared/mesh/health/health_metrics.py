"""
Health Metrics Collection System

Provides comprehensive metrics collection for the Datapunk service mesh health monitoring
system. Integrates with Prometheus for time-series metrics storage and visualization.

Key Features:
- Service health status tracking
- Dependency monitoring
- Resource usage metrics
- Latency tracking
- Failure rate monitoring

NOTE: This implementation assumes Prometheus is configured and accessible.
For local development, ensure Prometheus server is running and scraping enabled.
"""

from typing import Dict, Any, Optional
import structlog
from prometheus_client import Counter, Gauge, Histogram
from datetime import datetime

logger = structlog.get_logger()

class HealthMetrics:
    """
    Centralized metrics collection for service mesh health monitoring.
    
    Implements a comprehensive set of Prometheus metrics to track service health,
    dependencies, and resource usage. Designed to integrate with Grafana dashboards
    for visualization and alerting.
    
    TODO: Add metric retention policies
    TODO: Implement metric aggregation for cluster-wide health status
    """
    
    def __init__(self):
        """
        Initialize Prometheus metrics collectors.
        
        NOTE: Label cardinality is kept intentionally low to prevent metric explosion.
        Consider implications before adding new label dimensions.
        """
        # Track total checks and categorize by service and type
        self.check_total = Counter(
            'health_check_total',
            'Total number of health checks performed',
            ['service', 'check_type']
        )
        
        # Separate counter for failures to enable failure rate calculations
        self.check_failures = Counter(
            'health_check_failures_total',
            'Total number of health check failures',
            ['service', 'check_type', 'status']
        )
        
        # Current health status using tri-state value for granular health reporting
        self.health_status = Gauge(
            'service_health_status',
            'Current health status (0=unhealthy, 1=degraded, 2=healthy)',
            ['service', 'check_type']
        )
        
        # Track dependency health separately to identify cascade failures
        self.dependency_health = Gauge(
            'dependency_health_status',
            'Current health status of dependencies',
            ['service', 'dependency']
        )
        
        # Resource metrics for capacity planning and bottleneck detection
        self.resource_usage = Gauge(
            'resource_health_usage',
            'Resource usage metrics from health checks',
            ['service', 'resource_type']
        )
        
        # Latency histograms for performance tracking and SLO monitoring
        self.check_duration = Histogram(
            'health_check_duration_seconds',
            'Time spent performing health checks',
            ['service', 'check_type'],
            # Standard buckets optimized for typical health check durations
            buckets=[.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0]
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
        """
        Record comprehensive health check results.
        
        Captures multiple aspects of a health check execution including status,
        duration, and optional resource metrics. This data enables both real-time
        monitoring and historical trend analysis.
        
        Args:
            service: Service identifier
            check_type: Type of health check performed
            status: Health status (healthy/degraded/unhealthy)
            duration: Check execution time in seconds
            details: Optional resource usage metrics
        """
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