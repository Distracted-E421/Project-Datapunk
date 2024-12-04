"""
Authentication Metrics Collection System

Provides comprehensive monitoring of authentication and authorization
activities across the Datapunk service mesh. Integrates with Prometheus
for real-time security metrics collection and anomaly detection.

Key metrics:
- Authentication success/failure rates
- Token verification statistics
- Rate limit monitoring
- Active service tracking
- Latency measurements

See sys-arch.mmd Infrastructure/Observability for integration details.
"""

from typing import Dict, Any
import time
import logging
from dataclasses import dataclass, field
from prometheus_client import Counter, Histogram, Gauge

@dataclass
class AuthMetricsData:
    """
    Container for authentication-related metrics.
    
    Aggregates security metrics using Prometheus collectors for
    real-time monitoring and alerting. Metrics are labeled by
    service_id for granular analysis.
    
    TODO: Add metrics for credential rotation events
    TODO: Implement authentication pattern analysis
    """
    successful_auths: Counter = field(default_factory=lambda: Counter(
        'service_auth_successful_total',
        'Total number of successful service authentications',
        ['service_id']
    ))
    failed_auths: Counter = field(default_factory=lambda: Counter(
        'service_auth_failed_total',
        'Total number of failed service authentications',
        ['service_id', 'failure_reason']
    ))
    token_verifications: Counter = field(default_factory=lambda: Counter(
        'jwt_token_verifications_total',
        'Total number of JWT token verifications',
        ['service_id', 'status']
    ))
    auth_latency: Histogram = field(default_factory=lambda: Histogram(
        'service_auth_latency_seconds',
        'Service authentication latency in seconds',
        ['service_id', 'operation']
    ))
    rate_limit_exceeded: Counter = field(default_factory=lambda: Counter(
        'rate_limit_exceeded_total',
        'Total number of rate limit exceeded events',
        ['service_id']
    ))
    rate_limit_current: Gauge = field(default_factory=lambda: Gauge(
        'rate_limit_current',
        'Current rate limit usage',
        ['service_id', 'limit_type']
    ))
    active_services: Gauge = field(default_factory=lambda: Gauge(
        'auth_active_services',
        'Number of currently active authenticated services'
    ))

class AuthMetrics:
    """
    Authentication metrics collection and management.
    
    Provides methods for recording and tracking authentication-related
    events and performance metrics. Designed for integration with
    Prometheus/Grafana monitoring stack.
    
    NOTE: All methods are async to prevent blocking during high-volume
    metric collection.
    """
    def __init__(self):
        """
        Initialize metrics collectors.
        
        NOTE: Metrics are initialized lazily to prevent prometheus
        collector registration conflicts.
        """
        self.metrics = AuthMetricsData()
        self.logger = logging.getLogger(__name__)

    async def record_service_registration(self, service_id: str) -> None:
        """
        Track new service registrations.
        
        Updates active service count for capacity planning and
        security monitoring.
        
        NOTE: Counter increments are atomic to ensure accurate
        service counts.
        """
        try:
            self.metrics.active_services.inc()
        except Exception as e:
            self.logger.error(f"Failed to record service registration metric: {str(e)}")

    async def record_successful_auth(self, service_id: str) -> None:
        """
        Record successful authentication events.
        
        Tracks successful authentications for security pattern
        analysis and anomaly detection.
        
        TODO: Add authentication source tracking
        """
        try:
            self.metrics.successful_auths.labels(service_id=service_id).inc()
        except Exception as e:
            self.logger.error(f"Failed to record successful auth metric: {str(e)}")

    async def record_failed_auth(self, service_id: str, reason: str = "unknown") -> None:
        """
        Record failed authentication attempts.
        
        Captures authentication failures with reason codes for
        security analysis and threat detection.
        
        NOTE: Failure reasons are standardized for consistent
        analysis. See documentation for valid reason codes.
        """
        try:
            self.metrics.failed_auths.labels(
                service_id=service_id,
                failure_reason=reason
            ).inc()
        except Exception as e:
            self.logger.error(f"Failed to record failed auth metric: {str(e)}")

    async def record_auth_latency(
        self,
        service_id: str,
        operation: str,
        start_time: float
    ) -> None:
        """
        Track authentication operation timing.
        
        Measures authentication performance for SLA monitoring
        and performance optimization.
        
        NOTE: Uses high-precision time for accurate latency
        measurement.
        """
        try:
            duration = time.time() - start_time
            self.metrics.auth_latency.labels(
                service_id=service_id,
                operation=operation
            ).observe(duration)
        except Exception as e:
            self.logger.error(f"Failed to record auth latency metric: {str(e)}")

    async def record_successful_token_verification(self, service_id: str) -> None:
        """Record successful token verification"""
        try:
            self.metrics.token_verifications.labels(
                service_id=service_id,
                status="success"
            ).inc()
        except Exception as e:
            self.logger.error(f"Failed to record token verification metric: {str(e)}")

    async def record_failed_token_verification(
        self,
        service_id: str,
        reason: str = "invalid"
    ) -> None:
        """Record failed token verification"""
        try:
            self.metrics.token_verifications.labels(
                service_id=service_id,
                status=f"failed_{reason}"
            ).inc()
        except Exception as e:
            self.logger.error(f"Failed to record token verification metric: {str(e)}")

    async def record_rate_limit_exceeded(self, service_id: str) -> None:
        """Record rate limit exceeded event"""
        try:
            self.metrics.rate_limit_exceeded.labels(service_id=service_id).inc()
        except Exception as e:
            self.logger.error(f"Failed to record rate limit metric: {str(e)}")

    async def update_rate_limit_usage(
        self,
        service_id: str,
        usage: Dict[str, float]
    ) -> None:
        """Update current rate limit usage metrics"""
        try:
            for limit_type, value in usage.items():
                self.metrics.rate_limit_current.labels(
                    service_id=service_id,
                    limit_type=limit_type
                ).set(value)
        except Exception as e:
            self.logger.error(f"Failed to update rate limit usage metric: {str(e)}") 