"""
Extended Policy Tests
------------------

Tests the extended policy features including:
- Advanced compliance controls
- Geographic restrictions
- Service mesh integration
- Machine learning policy adaptation
- Policy inheritance and composition
- Dynamic policy updates

Run with: pytest -v test_policies_extended.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
import ipaddress

from datapunk_shared.auth.api_keys import (
    KeyPolicy, KeyType, ComplianceRequirements,
    SecurityControls, ResourceQuota, TimeWindow
)
from datapunk_shared.auth.api_keys.policies_extended import (
    GeoPolicy, ServiceMeshPolicy, AdaptivePolicy,
    ComplianceExtensions, SecurityExtensions,
    PolicyComposer, DynamicPolicyUpdater
)

# Test Fixtures

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.gauge = AsyncMock()
    return client

@pytest.fixture
def geo_service():
    """Mock geo-location service."""
    service = AsyncMock()
    service.get_country = AsyncMock(return_value="US")
    service.get_region = AsyncMock(return_value="us-west")
    return service

@pytest.fixture
def mesh_client():
    """Mock service mesh client."""
    client = AsyncMock()
    client.get_service_health = AsyncMock(return_value={"healthy": True})
    client.get_circuit_state = AsyncMock(return_value="closed")
    return client

@pytest.fixture
def ml_client():
    """Mock machine learning client for policy adaptation."""
    client = AsyncMock()
    client.predict_risk = AsyncMock(return_value=0.1)
    client.get_recommendations = AsyncMock()
    return client

# Geographic Policy Tests

@pytest.mark.asyncio
async def test_geo_policy_country_restriction(geo_service):
    """Test country-based access restrictions."""
    policy = GeoPolicy(
        allowed_countries={"US", "CA"},
        allowed_regions={"us-west", "ca-central"},
        geo_service=geo_service
    )
    
    # Allowed country
    assert await policy.validate_location("192.168.1.1")
    
    # Blocked country
    geo_service.get_country.return_value = "CN"
    assert not await policy.validate_location("192.168.1.2")

@pytest.mark.asyncio
async def test_geo_policy_region_restriction(geo_service):
    """Test region-based access restrictions."""
    policy = GeoPolicy(
        allowed_regions={"us-west"},
        geo_service=geo_service
    )
    
    # Allowed region
    assert await policy.validate_location("192.168.1.1")
    
    # Blocked region
    geo_service.get_region.return_value = "us-east"
    assert not await policy.validate_location("192.168.1.2")

@pytest.mark.asyncio
async def test_geo_policy_ip_ranges(geo_service):
    """Test IP range restrictions."""
    policy = GeoPolicy(
        allowed_ip_ranges=[
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("10.0.0.0/8")
        ],
        geo_service=geo_service
    )
    
    # Allowed IP
    assert await policy.validate_location("192.168.1.1")
    assert await policy.validate_location("10.0.0.1")
    
    # Blocked IP
    assert not await policy.validate_location("172.16.0.1")

# Service Mesh Policy Tests

@pytest.mark.asyncio
async def test_service_mesh_health_check(mesh_client):
    """Test service health-based policy."""
    policy = ServiceMeshPolicy(
        service_name="test_service",
        mesh_client=mesh_client
    )
    
    # Healthy service
    assert await policy.validate_service_health()
    
    # Unhealthy service
    mesh_client.get_service_health.return_value = {"healthy": False}
    assert not await policy.validate_service_health()

@pytest.mark.asyncio
async def test_service_mesh_circuit_breaker(mesh_client):
    """Test circuit breaker integration."""
    policy = ServiceMeshPolicy(
        service_name="test_service",
        mesh_client=mesh_client,
        respect_circuit_breaker=True
    )
    
    # Circuit closed
    assert await policy.validate_circuit_state()
    
    # Circuit open
    mesh_client.get_circuit_state.return_value = "open"
    assert not await policy.validate_circuit_state()

@pytest.mark.asyncio
async def test_service_mesh_load_balancing(mesh_client):
    """Test load balancing policy."""
    policy = ServiceMeshPolicy(
        service_name="test_service",
        mesh_client=mesh_client,
        max_concurrent_requests=100
    )
    
    # Under limit
    mesh_client.get_current_requests.return_value = 50
    assert await policy.validate_load()
    
    # Over limit
    mesh_client.get_current_requests.return_value = 150
    assert not await policy.validate_load()

# Adaptive Policy Tests

@pytest.mark.asyncio
async def test_adaptive_policy_risk_based(ml_client):
    """Test risk-based policy adaptation."""
    policy = AdaptivePolicy(
        base_policy=KeyPolicy(type=KeyType.SERVICE),
        ml_client=ml_client,
        risk_threshold=0.5
    )
    
    # Low risk - allow
    assert await policy.validate_risk("test_key")
    
    # High risk - block
    ml_client.predict_risk.return_value = 0.8
    assert not await policy.validate_risk("test_key")

@pytest.mark.asyncio
async def test_adaptive_policy_learning(ml_client):
    """Test policy learning from usage patterns."""
    policy = AdaptivePolicy(
        base_policy=KeyPolicy(type=KeyType.SERVICE),
        ml_client=ml_client
    )
    
    # Record usage patterns
    await policy.record_usage(
        key_id="test_key",
        request_count=1000,
        error_rate=0.01,
        response_time=100
    )
    
    # Should update recommendations
    ml_client.update_model.assert_called_once()
    
    # Get policy recommendations
    recommendations = await policy.get_recommendations("test_key")
    assert "rate_limit" in recommendations
    assert "allowed_ips" in recommendations

@pytest.mark.asyncio
async def test_adaptive_policy_auto_adjustment(ml_client):
    """Test automatic policy adjustment."""
    policy = AdaptivePolicy(
        base_policy=KeyPolicy(type=KeyType.SERVICE),
        ml_client=ml_client,
        auto_adjust=True
    )
    
    # Simulate good behavior
    await policy.record_usage(
        key_id="test_key",
        request_count=100,
        error_rate=0.01,
        response_time=50
    )
    
    # Should increase limits
    assert policy.rate_limit > policy.base_policy.rate_limit
    
    # Simulate bad behavior
    await policy.record_usage(
        key_id="test_key",
        request_count=1000,
        error_rate=0.1,
        response_time=500
    )
    
    # Should decrease limits
    assert policy.rate_limit < policy.base_policy.rate_limit

# Compliance Extension Tests

def test_compliance_gdpr_requirements():
    """Test GDPR compliance requirements."""
    compliance = ComplianceExtensions(
        base_requirements=ComplianceRequirements(
            audit_level="detailed"
        )
    )
    
    # Enable GDPR mode
    compliance.enable_gdpr()
    
    assert compliance.requires_consent
    assert compliance.requires_data_protection
    assert compliance.retention_period <= timedelta(days=365)
    assert "gdpr" in compliance.active_frameworks

def test_compliance_hipaa_requirements():
    """Test HIPAA compliance requirements."""
    compliance = ComplianceExtensions(
        base_requirements=ComplianceRequirements(
            audit_level="detailed"
        )
    )
    
    # Enable HIPAA mode
    compliance.enable_hipaa()
    
    assert compliance.requires_encryption
    assert compliance.requires_audit_trail
    assert compliance.requires_access_controls
    assert "hipaa" in compliance.active_frameworks

def test_compliance_multi_framework():
    """Test multiple compliance framework support."""
    compliance = ComplianceExtensions(
        base_requirements=ComplianceRequirements(
            audit_level="detailed"
        )
    )
    
    # Enable multiple frameworks
    compliance.enable_gdpr()
    compliance.enable_hipaa()
    
    # Should enforce strictest requirements
    assert compliance.audit_level == "full"
    assert compliance.requires_encryption
    assert compliance.requires_consent
    assert len(compliance.active_frameworks) == 2

# Security Extension Tests

def test_security_zero_trust():
    """Test zero trust security model."""
    security = SecurityExtensions(
        base_controls=SecurityControls(
            require_https=True
        )
    )
    
    # Enable zero trust
    security.enable_zero_trust()
    
    assert security.require_authentication
    assert security.require_authorization
    assert security.session_lifetime == timedelta(minutes=30)
    assert security.require_device_verification

def test_security_defense_in_depth():
    """Test defense in depth strategy."""
    security = SecurityExtensions(
        base_controls=SecurityControls(
            require_https=True
        )
    )
    
    # Enable defense in depth
    security.enable_defense_in_depth()
    
    assert security.require_waf
    assert security.enable_rate_limiting
    assert security.enable_anomaly_detection
    assert len(security.security_layers) >= 3

# Policy Composition Tests

def test_policy_inheritance():
    """Test policy inheritance and override."""
    base_policy = KeyPolicy(
        type=KeyType.SERVICE,
        rate_limit=1000
    )
    
    child_policy = PolicyComposer.inherit(
        base_policy,
        overrides={
            "rate_limit": 2000,
            "allowed_paths": {"/api/v2/*"}
        }
    )
    
    assert child_policy.rate_limit == 2000
    assert child_policy.type == base_policy.type
    assert "/api/v2/*" in child_policy.allowed_paths

def test_policy_composition():
    """Test policy composition from multiple sources."""
    policies = [
        KeyPolicy(type=KeyType.SERVICE, rate_limit=1000),
        GeoPolicy(allowed_countries={"US"}),
        ServiceMeshPolicy(service_name="test")
    ]
    
    composed = PolicyComposer.compose(policies)
    
    assert composed.type == KeyType.SERVICE
    assert composed.rate_limit == 1000
    assert "US" in composed.allowed_countries
    assert composed.service_name == "test"

# Dynamic Policy Updates

@pytest.mark.asyncio
async def test_dynamic_policy_updates():
    """Test dynamic policy updates."""
    updater = DynamicPolicyUpdater(
        base_policy=KeyPolicy(type=KeyType.SERVICE)
    )
    
    # Update based on conditions
    await updater.update_policy(
        conditions={
            "error_rate": 0.05,
            "response_time": 200,
            "concurrent_requests": 50
        }
    )
    
    assert updater.current_policy.rate_limit != updater.base_policy.rate_limit
    assert len(updater.update_history) > 0

@pytest.mark.asyncio
async def test_policy_update_rollback():
    """Test policy update rollback."""
    updater = DynamicPolicyUpdater(
        base_policy=KeyPolicy(type=KeyType.SERVICE)
    )
    
    # Make updates
    await updater.update_policy({"error_rate": 0.05})
    original_rate_limit = updater.current_policy.rate_limit
    
    # Bad update
    await updater.update_policy({"error_rate": 0.5})
    
    # Should rollback
    await updater.rollback()
    assert updater.current_policy.rate_limit == original_rate_limit 