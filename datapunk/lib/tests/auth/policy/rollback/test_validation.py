import pytest
from unittest.mock import Mock
from datapunk_shared.auth.policy.rollback.validation import (
    RollbackRisk, RollbackValidationResult, RollbackValidator
)
from datapunk_shared.core.exceptions import ValidationError

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def rollback_validator(metrics_client):
    """Create a RollbackValidator instance with mock dependencies."""
    validator = RollbackValidator(metrics_client)
    # Mock internal validation methods
    validator._validate_resource_access = Mock()
    validator._validate_security_changes = Mock()
    validator._validate_compliance_changes = Mock()
    validator._assess_risk_level = Mock(return_value=RollbackRisk.LOW)
    return validator

@pytest.fixture
def current_policy():
    """Create a sample current policy."""
    return {
        "type": "access",
        "resources": ["resource1", "resource2"],
        "security": {
            "encryption": True,
            "mfa": True
        },
        "compliance": {
            "gdpr": True,
            "retention_days": 90
        }
    }

@pytest.fixture
def rollback_policy():
    """Create a sample rollback policy."""
    return {
        "type": "access",
        "resources": ["resource1"],
        "security": {
            "encryption": False,
            "mfa": False
        },
        "compliance": {
            "gdpr": False,
            "retention_days": 30
        }
    }

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
    """Test successful rollback validation."""
    # Setup
    rollback_validator._assess_risk_level.return_value = RollbackRisk.LOW
    
    # Execute
    result = await rollback_validator.validate_rollback(
        current_policy=current_policy,
        rollback_policy=rollback_policy,
        affected_keys=["key1", "key2"]
    )
    
    # Verify
    assert isinstance(result, RollbackValidationResult)
    assert result.is_valid is True
    assert result.risk_level == RollbackRisk.LOW
    rollback_validator._validate_resource_access.assert_called_once()
    rollback_validator._validate_security_changes.assert_called_once()
    rollback_validator._validate_compliance_changes.assert_called_once()

@pytest.mark.asyncio
async def test_validate_rollback_with_breaking_changes(rollback_validator, current_policy, rollback_policy):
    """Test rollback validation with breaking changes."""
    # Setup
    def add_breaking_change(*args):
        args[2].append("Breaking change 1")
    
    rollback_validator._validate_resource_access.side_effect = add_breaking_change
    rollback_validator._assess_risk_level.return_value = RollbackRisk.HIGH
    
    # Execute
    result = await rollback_validator.validate_rollback(
        current_policy=current_policy,
        rollback_policy=rollback_policy,
        affected_keys=["key1"]
    )
    
    # Verify
    assert result.is_valid is False
    assert result.risk_level == RollbackRisk.HIGH
    assert len(result.breaking_changes) == 1
    assert result.breaking_changes[0] == "Breaking change 1"

@pytest.mark.asyncio
async def test_validate_rollback_with_warnings(rollback_validator, current_policy, rollback_policy):
    """Test rollback validation with warnings."""
    # Setup
    def add_warning(*args):
        args[3].append("Warning 1")
    
    rollback_validator._validate_security_changes.side_effect = add_warning
    rollback_validator._assess_risk_level.return_value = RollbackRisk.MEDIUM
    
    # Execute
    result = await rollback_validator.validate_rollback(
        current_policy=current_policy,
        rollback_policy=rollback_policy,
        affected_keys=["key1"]
    )
    
    # Verify
    assert result.is_valid is True
    assert result.risk_level == RollbackRisk.MEDIUM
    assert len(result.warnings) == 1
    assert result.warnings[0] == "Warning 1"

@pytest.mark.asyncio
async def test_validate_rollback_with_recommendations(rollback_validator, current_policy, rollback_policy):
    """Test rollback validation with recommendations."""
    # Setup
    def add_recommendation(*args):
        args[4].append("Recommendation 1")
    
    rollback_validator._validate_compliance_changes.side_effect = add_recommendation
    
    # Execute
    result = await rollback_validator.validate_rollback(
        current_policy=current_policy,
        rollback_policy=rollback_policy,
        affected_keys=["key1"]
    )
    
    # Verify
    assert len(result.recommendations) == 1
    assert result.recommendations[0] == "Recommendation 1"

@pytest.mark.asyncio
async def test_validate_rollback_error_handling(rollback_validator, current_policy, rollback_policy):
    """Test error handling during rollback validation."""
    # Setup
    rollback_validator._validate_resource_access.side_effect = Exception("Validation error")
    
    # Execute and verify
    with pytest.raises(ValidationError, match="Rollback validation failed"):
        await rollback_validator.validate_rollback(
            current_policy=current_policy,
            rollback_policy=rollback_policy,
            affected_keys=["key1"]
        )

@pytest.mark.asyncio
async def test_validate_rollback_critical_risk(rollback_validator, current_policy, rollback_policy):
    """Test rollback validation with critical risk assessment."""
    # Setup
    def add_multiple_breaking_changes(*args):
        args[2].extend(["Breaking change 1", "Breaking change 2"])
    
    rollback_validator._validate_resource_access.side_effect = add_multiple_breaking_changes
    rollback_validator._assess_risk_level.return_value = RollbackRisk.CRITICAL
    
    # Execute
    result = await rollback_validator.validate_rollback(
        current_policy=current_policy,
        rollback_policy=rollback_policy,
        affected_keys=["key1", "key2", "key3"]
    )
    
    # Verify
    assert result.is_valid is False
    assert result.risk_level == RollbackRisk.CRITICAL
    assert len(result.breaking_changes) == 2 