from typing import Dict, Any
from prometheus_client import Counter, Gauge, Histogram
import time

class MetricsCollector:
    """Unified metrics collection for services"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        
        # Request metrics
        self.request_counter = Counter(
            'requests_total',
            'Total requests processed',
            ['service', 'endpoint', 'method', 'status']
        )
        
        self.request_duration = Histogram(
            'request_duration_seconds',
            'Request duration in seconds',
            ['service', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Resource metrics
        self.resource_usage = Gauge(
            'resource_usage',
            'Resource usage metrics',
            ['service', 'resource_type']
        )
        
        # Business metrics
        self.operation_counter = Counter(
            'operations_total',
            'Total operations performed',
            ['service', 'operation_type', 'status']
        )
    
    def track_request(self, endpoint: str, method: str, status: int, duration: float):
        """Track API request metrics"""
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
        """Track business operation metrics"""
        self.operation_counter.labels(
            service=self.service_name,
            operation_type=operation_type,
            status=status
        ).inc()
    
    def update_resource_usage(self, metrics: Dict[str, float]):
        """Update resource usage metrics"""
        for resource_type, value in metrics.items():
            self.resource_usage.labels(
                service=self.service_name,
                resource_type=resource_type
            ).set(value) 