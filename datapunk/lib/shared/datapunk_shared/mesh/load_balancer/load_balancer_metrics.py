from typing import Dict, Any
import structlog
from prometheus_client import Counter, Gauge, Histogram
from datetime import datetime

logger = structlog.get_logger()

class LoadBalancerMetrics:
    """Metrics collection for load balancer."""
    
    def __init__(self):
        # Request tracking
        self.requests_total = Counter(
            'load_balancer_requests_total',
            'Total number of load balanced requests',
            ['service', 'instance', 'strategy']
        )
        
        self.request_errors = Counter(
            'load_balancer_errors_total',
            'Total number of load balancing errors',
            ['service', 'error_type']
        )
        
        # Instance health
        self.instance_health = Gauge(
            'load_balancer_instance_health',
            'Health score of service instances',
            ['service', 'instance']
        )
        
        self.active_instances = Gauge(
            'load_balancer_active_instances',
            'Number of active instances per service',
            ['service']
        )
        
        # Performance metrics
        self.request_duration = Histogram(
            'load_balancer_request_duration_seconds',
            'Request duration through load balancer',
            ['service', 'instance']
        )
        
        self.instance_load = Gauge(
            'load_balancer_instance_load',
            'Current load on each instance',
            ['service', 'instance']
        )
        
        # Connection tracking
        self.active_connections = Gauge(
            'load_balancer_active_connections',
            'Number of active connections per instance',
            ['service', 'instance']
        )
        
        self.connection_errors = Counter(
            'load_balancer_connection_errors_total',
            'Total number of connection errors',
            ['service', 'instance', 'error_type']
        )
    
    def record_request(self,
                      service: str,
                      instance: str,
                      strategy: str,
                      duration: float):
        """Record a load balanced request."""
        self.requests_total.labels(
            service=service,
            instance=instance,
            strategy=strategy
        ).inc()
        
        self.request_duration.labels(
            service=service,
            instance=instance
        ).observe(duration)
    
    def record_error(self,
                    service: str,
                    error_type: str):
        """Record a load balancing error."""
        self.request_errors.labels(
            service=service,
            error_type=error_type
        ).inc()
    
    def update_instance_health(self,
                             service: str,
                             instance: str,
                             health_score: float):
        """Update instance health score."""
        self.instance_health.labels(
            service=service,
            instance=instance
        ).set(health_score)
    
    def update_active_instances(self,
                              service: str,
                              count: int):
        """Update count of active instances."""
        self.active_instances.labels(
            service=service
        ).set(count)
    
    def update_instance_load(self,
                           service: str,
                           instance: str,
                           load: float):
        """Update instance load metric."""
        self.instance_load.labels(
            service=service,
            instance=instance
        ).set(load)
    
    def update_connections(self,
                         service: str,
                         instance: str,
                         connections: int):
        """Update active connection count."""
        self.active_connections.labels(
            service=service,
            instance=instance
        ).set(connections)
    
    def record_connection_error(self,
                              service: str,
                              instance: str,
                              error_type: str):
        """Record a connection error."""
        self.connection_errors.labels(
            service=service,
            instance=instance,
            error_type=error_type
        ).inc() 