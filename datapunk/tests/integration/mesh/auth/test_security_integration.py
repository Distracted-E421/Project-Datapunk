import pytest
import asyncio
import time
from typing import Dict, Any
from datetime import datetime, timedelta
from pathlib import Path

from datapunk_shared.mesh.auth.service_auth import ServiceAuthenticator, ServiceCredentials
from datapunk_shared.mesh.auth.rate_limiter import RateLimiter, RateLimitConfig
from datapunk_shared.mesh.auth.access_control import (
    AccessController, AccessPolicy, Resource, Permission
)
from datapunk_shared.mesh.auth.security_audit import SecurityAuditor, AuditEvent, AuditEventType
from datapunk_shared.mesh.auth.threat_detection import (
    ThreatDetector, ThreatEvent, ThreatLevel
)
from datapunk_shared.mesh.auth.security_metrics import SecurityMetrics

@pytest.fixture
async def security_components():
    """Setup security components for testing"""
    # Create temporary paths for testing
    test_dir = Path("/tmp/datapunk_test")
    test_dir.mkdir(exist_ok=True)
    
    credentials_dir = test_dir / "credentials"
    credentials_dir.mkdir(exist_ok=True)
    
    # Initialize components
    security_metrics = SecurityMetrics()
    security_auditor = SecurityAuditor(str(test_dir / "security_audit.log"))
    authenticator = ServiceAuthenticator(credentials_dir, "test_secret")
    rate_limiter = RateLimiter()
    access_controller = AccessController()
    threat_detector = ThreatDetector(security_metrics, security_auditor)
    
    yield {
        'metrics': security_metrics,
        'auditor': security_auditor,
        'authenticator': authenticator,
        'rate_limiter': rate_limiter,
        'access_controller': access_controller,
        'threat_detector': threat_detector,
        'test_dir': test_dir
    }
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)

@pytest.mark.asyncio
async def test_security_workflow(security_components):
    """Test complete security workflow"""
    # Setup test data
    service_id = "test_service"
    source_ip = "192.168.1.1"
    
    # Configure rate limiting
    await security_components['rate_limiter'].configure_limit(
        service_id,
        RateLimitConfig(
            requests_per_second=5,
            burst_size=10
        )
    )
    
    # Configure access policy
    policy = AccessPolicy(
        service_id=service_id,
        permissions={
            Resource.SERVICE: {Permission.READ, Permission.WRITE},
            Resource.METRICS: {Permission.READ}
        },
        ip_whitelist=[source_ip]
    )
    await security_components['access_controller'].add_policy(policy)
    
    # Test successful access
    access_result = await security_components['access_controller'].check_access(
        service_id,
        Resource.SERVICE,
        Permission.READ,
        source_ip
    )
    assert access_result is True
    
    # Test rate limiting
    for _ in range(15):  # Exceed rate limit
        allowed, _ = await security_components['rate_limiter'].check_rate_limit(service_id)
        if not allowed:
            # Process potential threat
            await security_components['threat_detector'].process_event(
                ThreatEvent(
                    service_id=service_id,
                    source_ip=source_ip,
                    event_type="rate_limit",
                    timestamp=time.time(),
                    details={"attempt": "rate_limit_breach"}
                )
            )
    
    # Verify threat detection
    threat_event = ThreatEvent(
        service_id=service_id,
        source_ip=source_ip,
        event_type="auth_failure",
        timestamp=time.time(),
        details={"reason": "repeated_failures"}
    )
    
    threat_level = await security_components['threat_detector'].process_event(threat_event)
    assert threat_level is not None

@pytest.mark.asyncio
async def test_threat_detection_escalation(security_components):
    """Test threat detection escalation logic"""
    service_id = "test_service"
    source_ip = "192.168.1.2"
    
    # Generate multiple authentication failures
    for _ in range(6):
        await security_components['threat_detector'].process_event(
            ThreatEvent(
                service_id=service_id,
                source_ip=source_ip,
                event_type="auth_failure",
                timestamp=time.time(),
                details={"attempt": "failed_login"}
            )
        )
    
    # Verify IP is blocked
    assert source_ip in security_components['threat_detector'].blocked_ips

@pytest.mark.asyncio
async def test_security_metrics_collection(security_components):
    """Test security metrics collection"""
    service_id = "test_service"
    
    # Record various security events
    await security_components['metrics'].record_auth_attempt(
        service_id=service_id,
        auth_type="jwt",
        success=True,
        duration=0.1
    )
    
    await security_components['metrics'].record_suspicious_activity(
        service_id=service_id,
        activity_type="unusual_access_pattern",
        details={"source": "test"}
    )
    
    # Verify metrics were collected
    # Note: In a real test, you'd want to verify the actual Prometheus metrics
    # This would require setting up a metrics endpoint and querying it

@pytest.mark.asyncio
async def test_audit_logging(security_components):
    """Test audit logging functionality"""
    service_id = "test_service"
    
    # Create audit event
    audit_event = AuditEvent(
        event_type=AuditEventType.CONFIG_CHANGE,
        service_id=service_id,
        timestamp=time.time(),
        details={"change": "security_policy_update"},
        severity="INFO"
    )
    
    # Log event
    await security_components['auditor'].log_event(audit_event)
    
    # Verify log file exists and contains the event
    log_path = security_components['test_dir'] / "security_audit.log"
    assert log_path.exists()
    with open(log_path) as f:
        log_content = f.read()
        assert service_id in log_content
        assert "security_policy_update" in log_content 