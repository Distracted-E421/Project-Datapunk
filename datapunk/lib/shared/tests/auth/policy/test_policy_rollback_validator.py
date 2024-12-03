import pytest
from unittest.mock import Mock
from datapunk_shared.auth.policy.policy_rollback_validator import (
    RollbackRisk, RollbackValidationResult, PolicyRollbackValidator
)
from datapunk_shared.auth.api_keys.policies_extended import (
    AdvancedKeyPolicy, ResourceType, CompliancePolicy
)
from datapunk_shared.exceptions import ValidationError

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def rollback_validator(metrics_client):
    """Create a PolicyRollbackValidator instance with mock dependencies."""
    return PolicyRollbackValidator(metrics_client)

@pytest.fixture
def current_policy():
    """Create a sample current policy."""
    return AdvancedKeyPolicy(
        type=ResourceType.API,
        allowed_resources={"resource1", "resource2", "resource3"},
        denied_resources={"denied1"},
        encryption_required=True,
        require_mfa=True,
        ip_whitelist=["10.0.0.0/24"],
        monitoring_level="debug",
        rate_limit=100,
        compliance=CompliancePolicy(
            encryption_required=True,
            audit_level="full",
            retention_period=90
        )
    )

@pytest.fixture
def rollback_policy():
    """Create a sample rollback policy."""
    return AdvancedKeyPolicy(
        type=ResourceType.API,
        allowed_resources={"resource1", "resource2"},
        denied_resources={"denied1", "denied2"},
        encryption_required=False,
        require_mfa=False,
        ip_whitelist=[],
        monitoring_level="info",
        rate_limit=50,
        compliance=CompliancePolicy(
            encryption_required=False,
            audit_level="basic",
            retention_period=30
        )
    )

def test_rollback_risk_enum():
    """Test RollbackRisk enum values."""
    assert RollbackRisk.LOW.value == "low"
    assert RollbackRisk.MEDIUM.value == "medium"
    assert RollbackRisk.HIGH.value == "high"
    assert RollbackRisk.CRITICAL.value == "critical"

def test_rollback_validation_result_creation():
    """Test RollbackValidationResult creation and properties."""
    result = RollbackValidationResult(
        is_valid=True,
        risk_level=RollbackRisk.LOW,
        breaking_changes=[],
        warnings=["Warning 1"],
        recommendations=["Recommendation 1"]
    )
    
    assert result.is_valid is True
    assert result.risk_level == RollbackRisk.LOW
    assert result.breaking_changes == []
    assert result.warnings == ["Warning 1"]
    assert result.recommendations == ["Recommendation 1"]

@pytest.mark.asyncio
async def test_validate_rollback_success(rollback_validator, current_policy, rollback_policy):
    """Test successful rollback validation with some warnings."""
    # Execute
    result = await rollback_validator.validate_rollback(
        current_policy,
        rollback_policy,
        affected_keys=["key1", "key2"]
    )
    
    # Verify
    assert isinstance(result, RollbackValidationResult)
    assert result.is_valid is False  # Should be False due to breaking changes
    assert len(result.breaking_changes) > 0
    assert len(result.warnings) > 0
    rollback_validator.metrics.increment.assert_called_once()

@pytest.mark.asyncio
async def test_validate_rollback_safe_changes(rollback_validator, current_policy):
    """Test validation of safe rollback changes."""
    # Setup - create a rollback policy with only safe changes
    safe_rollback = AdvancedKeyPolicy(
        type=ResourceType.API,
        allowed_resources={"resource1", "resource2", "resource3"},
        denied_resources={"denied1"},
        encryption_required=True,
        require_mfa=True,
        ip_whitelist=["10.0.0.0/24"],
        monitoring_level="debug",
        rate_limit=150,  # Only change is increased rate limit
        compliance=CompliancePolicy(
            encryption_required=True,
            audit_level="full",
            retention_period=90
        )
    )
    
    # Execute
    result = await rollback_validator.validate_rollback(
        current_policy,
        safe_rollback,
        affected_keys=["key1"]
    )
    
    # Verify
    assert result.is_valid is True
    assert len(result.breaking_changes) == 0
    assert result.risk_level == RollbackRisk.LOW

@pytest.mark.asyncio
async def test_validate_rollback_critical_changes(rollback_validator, current_policy):
    """Test validation of critical rollback changes."""
    # Setup - create a rollback policy with critical changes
    critical_rollback = AdvancedKeyPolicy(
        type=ResourceType.API,
        allowed_resources=set(),  # Remove all resource restrictions
        denied_resources=set(),
        encryption_required=False,  # Remove encryption
        require_mfa=False,  # Remove MFA
        ip_whitelist=[],
        monitoring_level="none",
        rate_limit=0,
        compliance=None  # Remove compliance settings
    )
    
    # Execute
    result = await rollback_validator.validate_rollback(
        current_policy,
        critical_rollback,
        affected_keys=["key1", "key2", "key3"]
    )
    
    # Verify
    assert result.is_valid is False
    assert len(result.breaking_changes) > 0
    assert result.risk_level == RollbackRisk.CRITICAL

@pytest.mark.asyncio
async def test_validate_rollback_large_scale(rollback_validator, current_policy, rollback_policy):
    """Test validation with large number of affected keys."""
    # Execute
    result = await rollback_validator.validate_rollback(
        current_policy,
        rollback_policy,
        affected_keys=["key" + str(i) for i in range(1001)]  # Over 1000 keys
    )
    
    # Verify
    assert result.risk_level in [RollbackRisk.HIGH, RollbackRisk.CRITICAL]

@pytest.mark.asyncio
async def test_validate_rollback_error_handling(rollback_validator, current_policy):
    """Test error handling during validation."""
    # Setup - create an invalid rollback policy to trigger error
    invalid_rollback = None
    
    # Execute and verify
    with pytest.raises(ValidationError):
        await rollback_validator.validate_rollback(
            current_policy,
            invalid_rollback,
            affected_keys=["key1"]
        )

def test_validate_resource_access(rollback_validator, current_policy, rollback_policy):
    """Test validation of resource access changes."""
    breaking_changes = []
    warnings = []
    
    # Execute
    rollback_validator._validate_resource_access(
        current_policy,
        rollback_policy,
        breaking_changes,
        warnings
    )
    
    # Verify
    assert any("removes access to resources" in change for change in breaking_changes)
    assert any("adds new resource restrictions" in warning for warning in warnings)

def test_validate_security_changes(rollback_validator, current_policy, rollback_policy):
    """Test validation of security control changes."""
    breaking_changes = []
    warnings = []
    recommendations = []
    
    # Execute
    rollback_validator._validate_security_changes(
        current_policy,
        rollback_policy,
        breaking_changes,
        warnings,
        recommendations
    )
    
    # Verify
    assert any("encryption requirement" in change for change in breaking_changes)
    assert any("MFA requirement" in change for change in breaking_changes)
    assert any("IP whitelist" in warning for warning in warnings)

def test_validate_compliance_changes(rollback_validator, current_policy, rollback_policy):
    """Test validation of compliance requirement changes."""
    breaking_changes = []
    warnings = []
    recommendations = []
    
    # Execute
    rollback_validator._validate_compliance_changes(
        current_policy,
        rollback_policy,
        breaking_changes,
        warnings,
        recommendations
    )
    
    # Verify
    assert any("compliance" in change for change in breaking_changes)
    assert any("audit logging" in warning for warning in warnings)
    assert any("retention period" in warning for warning in warnings) 