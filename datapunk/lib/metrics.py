"""Unified metrics collection system for Datapunk services.

This module implements a centralized metrics collection system that aligns with
the observability requirements outlined in sys-arch.mmd. It provides standardized
metrics collection across all services using Prometheus as the backend.

Key Metrics Categories:
- Request metrics: Track API performance and usage patterns
- Resource metrics: Monitor system resource utilization
- Business metrics: Measure service-specific operations

Implementation Notes:
- Uses Prometheus client library for compatibility with monitoring stack
- Metrics are labeled by service for multi-service aggregation
- Histogram buckets are optimized for typical request patterns
"""

from typing import Dict, Any
from prometheus_client import Counter, Gauge, Histogram
import time

class MetricsCollector:
    """Centralized metrics collection for service observability.
    
    Implements standardized metrics collection across all services:
    - Request tracking with duration histograms
    - Resource usage monitoring
    - Business operation counting
    
    Note: Metrics are automatically labeled with service_name for aggregation
    in Grafana dashboards as defined in the system architecture.
    """
    
    def __init__(self, service_name: str):
        """Initialize metrics collectors with service identification.
        
        Args:
            service_name: Unique identifier for this service instance
        
        Note: Histogram buckets are pre-configured for typical API response times
        TODO: Make histogram buckets configurable per service requirements
        """
        self.service_name = service_name
        
        # Request metrics with detailed dimensionality for analysis
        self.request_counter = Counter(
            'requests_total',
            'Total requests processed',
            ['service', 'endpoint', 'method', 'status']
        )
        
        # Duration tracking with optimized bucket sizes
        self.request_duration = Histogram(
            'request_duration_seconds',
            'Request duration in seconds',
            ['service', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]  # Covers typical API response times
        )
        
        # Resource tracking for capacity planning
        self.resource_usage = Gauge(
            'resource_usage',
            'Resource usage metrics',
            ['service', 'resource_type']
        )
        
        # Business metrics for operational insights
        self.operation_counter = Counter(
            'operations_total',
            'Total operations performed',
            ['service', 'operation_type', 'status']
        )
    
    def track_request(self, endpoint: str, method: str, status: int, duration: float):
        """Record API request metrics for monitoring and alerting.
        
        Tracks both request counts and duration distributions for:
        - Performance monitoring
        - SLA compliance
        - Capacity planning
        - Anomaly detection
        
        Args:
            endpoint: API endpoint path
            method: HTTP method used
            status: Response status code
            duration: Request processing time in seconds
        """
        self.request_counter.labels(
            service=self.service_name,
            endpoint=endpoint,
            method=method,
            status=status
        ).inc()
        
        self.request_duration.labels(
            service=self.service_name,
            endpoint=endpoint
        ).observe(duration)
    
    def track_operation(self, operation_type: str, status: str = 'success'):
        """Record business operation metrics for service monitoring.
        
        Used to track service-specific operations for:
        - Business analytics
        - Operation success rates
        - System usage patterns
        
        Args:
            operation_type: Type of business operation
            status: Operation outcome (default: 'success')
        """
        self.operation_counter.labels(
            service=self.service_name,
            operation_type=operation_type,
            status=status
        ).inc()
    
    def update_resource_usage(self, metrics: Dict[str, float]):
        """Update resource utilization metrics for capacity planning.
        
        Records current resource usage levels for:
        - Resource allocation optimization
        - Capacity planning
        - Cost analysis
        - Performance correlation
        
        Args:
            metrics: Dictionary of resource types and their current usage values
        """
        for resource_type, value in metrics.items():
            self.resource_usage.labels(
                service=self.service_name,
                resource_type=resource_type
            ).set(value) 