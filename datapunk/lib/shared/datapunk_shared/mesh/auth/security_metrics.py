from typing import Dict, Any
import time
import logging
from dataclasses import dataclass, field
from prometheus_client import Counter, Histogram, Gauge, Summary

@dataclass
class SecurityMetricsData:
    # Authentication Metrics
    auth_attempts: Counter = field(default_factory=lambda: Counter(
        'security_auth_attempts_total',
        'Total number of authentication attempts',
        ['service_id', 'auth_type', 'result']
    ))
    auth_latency: Histogram = field(default_factory=lambda: Histogram(
        'security_auth_latency_seconds',
        'Authentication operation latency',
        ['service_id', 'auth_type']
    ))
    
    # Certificate Metrics
    cert_expiry: Gauge = field(default_factory=lambda: Gauge(
        'security_cert_expiry_seconds',
        'Time until certificate expiration',
        ['service_id', 'cert_type']
    ))
    cert_rotations: Counter = field(default_factory=lambda: Counter(
        'security_cert_rotations_total',
        'Total number of certificate rotations',
        ['service_id', 'cert_type']
    ))
    
    # Access Control Metrics
    access_denied: Counter = field(default_factory=lambda: Counter(
        'security_access_denied_total',
        'Total number of denied access attempts',
        ['service_id', 'resource', 'reason']
    ))
    policy_changes: Counter = field(default_factory=lambda: Counter(
        'security_policy_changes_total',
        'Total number of security policy changes',
        ['service_id', 'change_type']
    ))
    
    # Threat Detection
    suspicious_activities: Counter = field(default_factory=lambda: Counter(
        'security_suspicious_activities_total',
        'Total number of suspicious activities detected',
        ['service_id', 'activity_type']
    ))
    blocked_ips: Gauge = field(default_factory=lambda: Gauge(
        'security_blocked_ips_total',
        'Number of currently blocked IPs',
        ['service_id']
    ))
    
    # Performance Impact
    security_overhead: Summary = field(default_factory=lambda: Summary(
        'security_processing_overhead_seconds',
        'Time overhead added by security processing',
        ['service_id', 'operation_type']
    ))

class SecurityMetrics:
    def __init__(self):
        self.metrics = SecurityMetricsData()
        self.logger = logging.getLogger(__name__)

    async def record_auth_attempt(
        self,
        service_id: str,
        auth_type: str,
        success: bool,
        duration: float
    ) -> None:
        """Record authentication attempt metrics"""
        try:
            self.metrics.auth_attempts.labels(
                service_id=service_id,
                auth_type=auth_type,
                result="success" if success else "failure"
            ).inc()
            
            self.metrics.auth_latency.labels(
                service_id=service_id,
                auth_type=auth_type
            ).observe(duration)
        except Exception as e:
            self.logger.error(f"Failed to record auth attempt metric: {str(e)}")

    async def update_cert_expiry(
        self,
        service_id: str,
        cert_type: str,
        expiry_time: float
    ) -> None:
        """Update certificate expiration metrics"""
        try:
            self.metrics.cert_expiry.labels(
                service_id=service_id,
                cert_type=cert_type
            ).set(expiry_time - time.time())
        except Exception as e:
            self.logger.error(f"Failed to update cert expiry metric: {str(e)}")

    async def record_suspicious_activity(
        self,
        service_id: str,
        activity_type: str,
        details: Dict[str, Any]
    ) -> None:
        """Record suspicious activity metrics"""
        try:
            self.metrics.suspicious_activities.labels(
                service_id=service_id,
                activity_type=activity_type
            ).inc()
        except Exception as e:
            self.logger.error(f"Failed to record suspicious activity metric: {str(e)}")

    async def record_security_overhead(
        self,
        service_id: str,
        operation_type: str,
        duration: float
    ) -> None:
        """Record security processing overhead metrics"""
        try:
            self.metrics.security_overhead.labels(
                service_id=service_id,
                operation_type=operation_type
            ).observe(duration)
        except Exception as e:
            self.logger.error(f"Failed to record security overhead metric: {str(e)}") 