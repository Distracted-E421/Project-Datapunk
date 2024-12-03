import pytest
from datetime import datetime, time
from datapunk_shared.auth.policy.types import (
    PolicyType, PolicyStatus, RiskLevel, TimeWindow,
    PolicyRule, Policy, PolicyValidationResult, PolicyEvaluationResult
)

def test_policy_type_enum():
    """Test PolicyType enum values and properties."""
    assert PolicyType.ACCESS.value == "access"
    assert PolicyType.AUTHENTICATION.value == "auth"
    assert PolicyType.ENCRYPTION.value == "encrypt"
    assert PolicyType.AUDIT.value == "audit"
    assert PolicyType.COMPLIANCE.value == "comply"
    assert PolicyType.ROTATION.value == "rotate"
    assert PolicyType.RATE_LIMIT.value == "rate"

def test_policy_status_enum():
    """Test PolicyStatus enum values and workflow states."""
    assert PolicyStatus.DRAFT.value == "draft"
    assert PolicyStatus.ACTIVE.value == "active"
    assert PolicyStatus.DISABLED.value == "disabled"
    assert PolicyStatus.ARCHIVED.value == "archived"
    assert PolicyStatus.PENDING.value == "pending"

def test_risk_level_enum():
    """Test RiskLevel enum values and classification."""
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.MEDIUM.value == "medium"
    assert RiskLevel.HIGH.value == "high"
    assert RiskLevel.CRITICAL.value == "critical"

def test_time_window_creation():
    """Test TimeWindow dataclass creation and properties."""
    window = TimeWindow(
        start_time=time(9, 0),
        end_time=time(17, 0),
        days={0, 1, 2, 3, 4},  # Monday through Friday
        timezone="UTC"
    )
    assert window.start_time == time(9, 0)
    assert window.end_time == time(17, 0)
    assert window.days == {0, 1, 2, 3, 4}
    assert window.timezone == "UTC"

def test_policy_rule_creation():
    """Test PolicyRule dataclass creation and properties."""
    rule = PolicyRule(
        rule_id="test-rule-001",
        rule_type="access_control",
        conditions={"role": "admin"},
        actions=["allow_access"],
        priority=1,
        metadata={"owner": "security_team"}
    )
    assert rule.rule_id == "test-rule-001"
    assert rule.rule_type == "access_control"
    assert rule.conditions == {"role": "admin"}
    assert rule.actions == ["allow_access"]
    assert rule.priority == 1
    assert rule.metadata == {"owner": "security_team"}

def test_policy_creation():
    """Test Policy dataclass creation and properties."""
    now = datetime.utcnow()
    policy = Policy(
        policy_id="test-policy-001",
        type=PolicyType.ACCESS,
        status=PolicyStatus.ACTIVE,
        rules=[],
        version="1.0.0",
        created_at=now,
        created_by="test_user",
        effective_from=now,
        description="Test policy",
        metadata={"department": "IT"}
    )
    assert policy.policy_id == "test-policy-001"
    assert policy.type == PolicyType.ACCESS
    assert policy.status == PolicyStatus.ACTIVE
    assert policy.rules == []
    assert policy.version == "1.0.0"
    assert policy.created_at == now
    assert policy.created_by == "test_user"
    assert policy.effective_from == now
    assert policy.description == "Test policy"
    assert policy.metadata == {"department": "IT"}

def test_policy_validation_result_creation():
    """Test PolicyValidationResult dataclass creation and properties."""
    result = PolicyValidationResult(
        valid=True,
        issues=[],
        warnings=["Review recommended"],
        risk_level=RiskLevel.LOW,
        breaking_changes=[],
        metadata={"validator": "automated_check"}
    )
    assert result.valid is True
    assert result.issues == []
    assert result.warnings == ["Review recommended"]
    assert result.risk_level == RiskLevel.LOW
    assert result.breaking_changes == []
    assert result.metadata == {"validator": "automated_check"}

def test_policy_evaluation_result_creation():
    """Test PolicyEvaluationResult dataclass creation and properties."""
    result = PolicyEvaluationResult(
        allowed=True,
        matched_rules=["rule-001"],
        reason="Access granted based on role",
        context={"user_role": "admin"},
        metadata={"timestamp": "2023-01-01T00:00:00Z"}
    )
    assert result.allowed is True
    assert result.matched_rules == ["rule-001"]
    assert result.reason == "Access granted based on role"
    assert result.context == {"user_role": "admin"}
    assert result.metadata == {"timestamp": "2023-01-01T00:00:00Z"}

def test_policy_rule_default_values():
    """Test PolicyRule default values."""
    rule = PolicyRule(
        rule_id="test-rule",
        rule_type="test",
        conditions={},
        actions=[]
    )
    assert rule.priority == 0
    assert rule.metadata is None

def test_policy_optional_fields():
    """Test Policy optional fields."""
    now = datetime.utcnow()
    policy = Policy(
        policy_id="test-policy",
        type=PolicyType.ACCESS,
        status=PolicyStatus.ACTIVE,
        rules=[],
        version="1.0.0",
        created_at=now,
        created_by="test_user",
        effective_from=now
    )
    assert policy.effective_until is None
    assert policy.description is None
    assert policy.metadata is None 