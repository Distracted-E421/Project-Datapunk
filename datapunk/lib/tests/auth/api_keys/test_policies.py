"""
API Key Policy Tests
------------------

Tests the policy framework for API keys including:
- Policy validation and enforcement
- Security controls
- Resource quotas
- Time window restrictions
- Circuit breaker integration
- Compliance requirements

Run with: pytest -v test_policies.py
"""

import pytest
from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock, Mock
import pytz

from datapunk_shared.auth.api_keys import (
    KeyType, KeyPolicy, ComplianceRequirements,
    SecurityControls, ResourceQuota, TimeWindow,
    CircuitBreaker
)

# Test Fixtures

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    return client

@pytest.fixture
def basic_policy():
    """Create basic policy for testing."""
    return KeyPolicy(
        type=KeyType.SERVICE,
        rate_limit=1000,
        allowed_paths={"/api/v1/*"},
        allowed_methods={"GET", "POST"}
    )

@pytest.fixture
def compliance_requirements():
    """Create compliance requirements for testing."""
    return ComplianceRequirements(
        require_mfa=True,
        audit_level="detailed",
        data_classification="restricted",
        retention_period=timedelta(days=90)
    )

@pytest.fixture
def security_controls():
    """Create security controls for testing."""
    return SecurityControls(
        require_https=True,
        require_client_certs=True,
        allowed_ips={"192.168.1.0/24"},
        encryption_required=True,
        min_tls_version="1.2"
    )

@pytest.fixture
def resource_quota():
    """Create resource quota for testing."""
    return ResourceQuota(
        daily_requests=10000,
        storage_mb=1000,
        concurrent_connections=100,
        bandwidth_mbps=50
    )

# Policy Type Tests

def test_key_type_hierarchy():
    """Test key type hierarchy and privileges."""
    assert KeyType.ADMIN.value > KeyType.SERVICE.value
    assert KeyType.SERVICE.value > KeyType.READ_ONLY.value
    assert KeyType.READ_ONLY.value > KeyType.LIMITED.value

def test_key_type_validation():
    """Test key type validation rules."""
    policy = KeyPolicy(type=KeyType.ADMIN)
    
    # Admin type requires stricter security
    assert policy.security.require_https is True
    assert policy.security.require_client_certs is True
    assert policy.compliance.audit_level == "full"

# Policy Validation Tests

def test_basic_policy_validation(basic_policy):
    """Test basic policy validation."""
    assert basic_policy.is_valid()
    assert basic_policy.rate_limit > 0
    assert basic_policy.allowed_paths
    assert basic_policy.allowed_methods

def test_policy_path_validation(basic_policy):
    """Test API path pattern validation."""
    # Valid patterns
    assert basic_policy.validate_path("/api/v1/users")
    assert basic_policy.validate_path("/api/v1/data/query")
    
    # Invalid patterns
    assert not basic_policy.validate_path("/api/v2/users")
    assert not basic_policy.validate_path("/internal/admin")

def test_policy_method_validation(basic_policy):
    """Test HTTP method validation."""
    # Valid methods
    assert basic_policy.validate_method("GET")
    assert basic_policy.validate_method("POST")
    
    # Invalid methods
    assert not basic_policy.validate_method("DELETE")
    assert not basic_policy.validate_method("PATCH")

# Compliance Tests

def test_compliance_requirements(compliance_requirements):
    """Test compliance requirement validation."""
    assert compliance_requirements.is_valid()
    assert compliance_requirements.meets_standard("SOC2")
    assert compliance_requirements.retention_period.days == 90

def test_compliance_audit_levels(compliance_requirements):
    """Test audit level requirements."""
    assert compliance_requirements.audit_level in {"minimal", "detailed", "full"}
    assert compliance_requirements.requires_audit_trail()

def test_data_classification(compliance_requirements):
    """Test data classification rules."""
    assert compliance_requirements.data_classification in {
        "public", "internal", "restricted", "confidential"
    }
    assert compliance_requirements.requires_encryption()

# Security Control Tests

def test_security_controls(security_controls):
    """Test security control validation."""
    assert security_controls.is_valid()
    assert security_controls.validate_tls_version("1.3")
    assert not security_controls.validate_tls_version("1.1")

def test_ip_restrictions(security_controls):
    """Test IP-based access restrictions."""
    assert security_controls.validate_ip("192.168.1.100")
    assert not security_controls.validate_ip("10.0.0.1")

def test_certificate_requirements(security_controls):
    """Test certificate validation requirements."""
    assert security_controls.require_client_certs
    assert security_controls.validate_cert_strength("RSA4096")
    assert not security_controls.validate_cert_strength("RSA1024")

# Resource Quota Tests

def test_resource_quota_validation(resource_quota):
    """Test resource quota validation."""
    assert resource_quota.is_valid()
    assert resource_quota.daily_requests > 0
    assert resource_quota.storage_mb > 0

def test_quota_consumption(resource_quota):
    """Test quota consumption tracking."""
    assert resource_quota.can_consume(requests=100)
    assert resource_quota.can_consume(storage_mb=50)
    assert not resource_quota.can_consume(bandwidth_mbps=100)

def test_quota_reset(resource_quota):
    """Test quota reset functionality."""
    resource_quota.consume(requests=5000)
    assert resource_quota.remaining_requests == 5000
    
    resource_quota.reset_daily_quotas()
    assert resource_quota.remaining_requests == 10000

# Time Window Tests

def test_time_window_validation():
    """Test time window restrictions."""
    window = TimeWindow(
        start_time=time(9, 0),
        end_time=time(17, 0),
        days={0, 1, 2, 3, 4},  # Monday-Friday
        timezone="UTC"
    )
    
    # Test time-based access
    business_hours = datetime.now(pytz.UTC).replace(
        hour=13,  # 1 PM
        minute=0
    )
    assert window.is_active(business_hours)
    
    # Test after-hours restriction
    after_hours = business_hours.replace(hour=20)  # 8 PM
    assert not window.is_active(after_hours)
    
    # Test weekend restriction
    weekend = business_hours + timedelta(days=2)
    if weekend.weekday() not in window.days:
        assert not window.is_active(weekend)

# Circuit Breaker Tests

def test_circuit_breaker_config():
    """Test circuit breaker configuration."""
    breaker = CircuitBreaker(
        failure_threshold=5,
        reset_timeout=300,
        half_open_max_calls=3
    )
    
    assert breaker.failure_threshold == 5
    assert breaker.reset_timeout == 300
    assert breaker.half_open_max_calls == 3

def test_circuit_breaker_state_machine():
    """Test circuit breaker state transitions."""
    breaker = CircuitBreaker(failure_threshold=2)
    
    # Initial state
    assert breaker.is_closed()
    
    # Open after failures
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.is_open()
    
    # Half-open after timeout
    breaker.last_failure_time -= timedelta(minutes=6)
    assert breaker.allow_request()
    assert breaker.is_half_open()

# Policy Template Tests

def test_analytics_policy():
    """Test analytics policy template."""
    policy = ANALYTICS_POLICY
    
    assert policy.type == KeyType.ANALYTICS
    assert "/api/v1/analytics/" in policy.allowed_paths
    assert policy.compliance.data_classification == "internal"

def test_emergency_policy():
    """Test emergency policy template."""
    policy = EMERGENCY_POLICY
    
    assert policy.type == KeyType.EMERGENCY
    assert policy.compliance.require_mfa
    assert policy.security.require_https
    assert policy.circuit_breaker.failure_threshold == 3

def test_temporary_policy():
    """Test temporary policy template."""
    policy = TEMPORARY_POLICY
    
    assert policy.type == KeyType.TEMPORARY
    assert len(policy.time_windows) == 1
    assert policy.quota.daily_requests == 1000
    
    window = policy.time_windows[0]
    assert window.start_time == time(9, 0)
    assert window.end_time == time(17, 0)
    assert set(window.days) == {0, 1, 2, 3, 4}  # Monday-Friday

# Integration Tests

def test_policy_composition():
    """Test combining multiple policy components."""
    policy = KeyPolicy(
        type=KeyType.SERVICE,
        rate_limit=1000,
        allowed_paths={"/api/v1/*"},
        allowed_methods={"GET", "POST"},
        compliance=ComplianceRequirements(
            require_mfa=True,
            audit_level="detailed"
        ),
        security=SecurityControls(
            require_https=True,
            allowed_ips={"192.168.1.0/24"}
        ),
        quota=ResourceQuota(
            daily_requests=10000,
            storage_mb=1000
        ),
        time_windows=[
            TimeWindow(
                start_time=time(9, 0),
                end_time=time(17, 0),
                days={0, 1, 2, 3, 4}
            )
        ],
        circuit_breaker=CircuitBreaker(
            failure_threshold=5,
            reset_timeout=300
        )
    )
    
    assert policy.is_valid()
    assert policy.validate_request(
        path="/api/v1/data",
        method="GET",
        client_ip="192.168.1.100",
        timestamp=datetime.now().replace(hour=14),
        https=True
    ) 