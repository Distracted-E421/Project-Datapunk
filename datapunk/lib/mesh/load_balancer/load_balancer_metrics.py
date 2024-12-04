"""
Load Balancer Metrics Collection System

Provides comprehensive metrics tracking for the Datapunk load balancer,
integrating with Prometheus for time-series data collection and visualization.
Designed to support performance monitoring, debugging, and capacity planning.

Key Metrics Categories:
- Request tracking and errors
- Instance health and availability
- Performance measurements
- Connection monitoring

NOTE: Label cardinality should be monitored as high cardinality
can impact Prometheus performance. Consider aggregation for large deployments.

TODO: Add metric retention policies
TODO: Implement metric aggregation for cluster-wide statistics
"""

from typing import Dict, Any
import structlog
from prometheus_client import Counter, Gauge, Histogram
from datetime import datetime

logger = structlog.get_logger()

class LoadBalancerMetrics:
    """
    Centralized metrics collection for load balancer operations.
    
    Implements Prometheus metrics collectors for comprehensive monitoring
    of load balancer behavior, performance, and health. Designed to integrate
    with Grafana dashboards for visualization and alerting.
    
    IMPORTANT: High-cardinality labels (like instance IDs) should be used
    judiciously to prevent metric explosion in large deployments.
    """
    
    def __init__(self):
        """
        Initialize Prometheus metrics collectors.
        
        Metrics are organized into four main categories:
        1. Request metrics - Track request flow and errors
        2. Health metrics - Monitor instance health
        3. Performance metrics - Measure timing and load
        4. Connection metrics - Track connection states
        """
        # Request tracking with detailed labels for analysis
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
        
        # Health tracking for instance selection
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
        
        # Performance metrics with histogram for percentile analysis
        self.request_duration = Histogram(
            'load_balancer_request_duration_seconds',
            'Request duration through load balancer',
            ['service', 'instance'],
            buckets=[.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0]
        )
        
        self.instance_load = Gauge(
            'load_balancer_instance_load',
            'Current load on each instance',
            ['service', 'instance']
        )
        
        # Connection state tracking
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
        """
        Record metrics for a completed request.
        
        Tracks both request count and duration for performance analysis.
        Duration buckets are optimized for typical microservice latencies.
        """
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
        """
        Record load balancing errors for monitoring and alerting.
        
        Error types should be standardized across the system for
        consistent tracking and analysis.
        """
        self.request_errors.labels(
            service=service,
            error_type=error_type
        ).inc()
    
    def update_instance_health(self,
                             service: str,
                             instance: str,
                             health_score: float):
        """
        Update instance health score for load balancing decisions.
        
        Health scores should be normalized between 0 and 1:
        - 0: Completely unhealthy
        - 1: Fully healthy
        """
        self.instance_health.labels(
            service=service,
            instance=instance
        ).set(health_score)
    
    def update_active_instances(self,
                              service: str,
                              count: int):
        """
        Update active instance count for capacity monitoring.
        
        Critical for auto-scaling and capacity planning decisions.
        Should be called after instance registration/deregistration.
        """
        self.active_instances.labels(
            service=service
        ).set(count)
    
    def update_instance_load(self,
                           service: str,
                           instance: str,
                           load: float):
        """
        Update instance load metric for balancing decisions.
        
        Load should be normalized between 0 and 1:
        - 0: No load
        - 1: Maximum load
        """
        self.instance_load.labels(
            service=service,
            instance=instance
        ).set(load)
    
    def update_connections(self,
                         service: str,
                         instance: str,
                         connections: int):
        """
        Update active connection count for capacity monitoring.
        
        Important for detecting connection leaks and capacity issues.
        Should be called regularly to maintain accuracy.
        """
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