from typing import Dict, Any
import time
import logging
from dataclasses import dataclass, field
from prometheus_client import Counter, Histogram, Gauge

@dataclass
class AuthMetricsData:
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
    def __init__(self):
        self.metrics = AuthMetricsData()
        self.logger = logging.getLogger(__name__)

    async def record_service_registration(self, service_id: str) -> None:
        """Record service registration metrics"""
        try:
            self.metrics.active_services.inc()
        except Exception as e:
            self.logger.error(f"Failed to record service registration metric: {str(e)}")

    async def record_successful_auth(self, service_id: str) -> None:
        """Record successful authentication"""
        try:
            self.metrics.successful_auths.labels(service_id=service_id).inc()
        except Exception as e:
            self.logger.error(f"Failed to record successful auth metric: {str(e)}")

    async def record_failed_auth(self, service_id: str, reason: str = "unknown") -> None:
        """Record failed authentication"""
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
        """Record authentication operation latency"""
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