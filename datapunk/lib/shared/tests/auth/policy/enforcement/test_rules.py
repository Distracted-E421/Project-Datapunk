import pytest
from datetime import datetime, time
from unittest.mock import Mock, AsyncMock
from datapunk_shared.auth.policy.enforcement.rules import (
    RuleType, EnforcementRule, TimeBasedRule, RateLimitRule, RuleEngine
)
from datapunk_shared.auth.policy.types import (
    PolicyType, PolicyStatus, TimeWindow
)
from datapunk_shared.core.exceptions import AuthError

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def rule_engine(metrics_client):
    """Create a RuleEngine instance with mock dependencies."""
    return RuleEngine(metrics_client)

@pytest.fixture
def time_based_rule():
    """Create a sample time-based rule."""
    return TimeBasedRule(
        type=RuleType.TIME_BASED,
        policy_type=PolicyType.ACCESS,
        status=PolicyStatus.ACTIVE,
        priority=1,
        windows=[
            TimeWindow(
                start_time=time(9, 0),
                end_time=time(17, 0),
                days={0, 1, 2, 3, 4},  # Monday through Friday
                timezone="UTC"
            )
        ],
        timezone="UTC"
    )

@pytest.fixture
def rate_limit_rule():
    """Create a sample rate limit rule."""
    return RateLimitRule(
        type=RuleType.RATE_LIMIT,
        policy_type=PolicyType.ACCESS,
        status=PolicyStatus.ACTIVE,
        priority=2,
        requests_per_second=10,
        burst_size=20,
        window_size=60
    )

def test_rule_type_enum():
    """Test RuleType enum values."""
    assert RuleType.TIME_BASED.value == "time_based"
    assert RuleType.RATE_LIMIT.value == "rate_limit"
    assert RuleType.GEO_LOCATION.value == "geo_location"
    assert RuleType.RESOURCE_ACCESS.value == "resource_access"
    assert RuleType.COMPLIANCE.value == "compliance"

def test_enforcement_rule_creation():
    """Test EnforcementRule creation and properties."""
    rule = EnforcementRule(
        type=RuleType.TIME_BASED,
        policy_type=PolicyType.ACCESS,
        status=PolicyStatus.ACTIVE,
        priority=1
    )
    
    assert rule.type == RuleType.TIME_BASED
    assert rule.policy_type == PolicyType.ACCESS
    assert rule.status == PolicyStatus.ACTIVE
    assert rule.priority == 1

def test_time_based_rule_creation():
    """Test TimeBasedRule creation and properties."""
    window = TimeWindow(
        start_time=time(9, 0),
        end_time=time(17, 0),
        days={0, 1, 2, 3, 4},
        timezone="UTC"
    )
    
    rule = TimeBasedRule(
        type=RuleType.TIME_BASED,
        policy_type=PolicyType.ACCESS,
        windows=[window],
        timezone="UTC"
    )
    
    assert rule.type == RuleType.TIME_BASED
    assert len(rule.windows) == 1
    assert rule.timezone == "UTC"
    assert rule.windows[0].start_time == time(9, 0)
    assert rule.windows[0].end_time == time(17, 0)

def test_rate_limit_rule_creation():
    """Test RateLimitRule creation and properties."""
    rule = RateLimitRule(
        type=RuleType.RATE_LIMIT,
        policy_type=PolicyType.ACCESS,
        requests_per_second=10,
        burst_size=20,
        window_size=60
    )
    
    assert rule.type == RuleType.RATE_LIMIT
    assert rule.requests_per_second == 10
    assert rule.burst_size == 20
    assert rule.window_size == 60

@pytest.mark.asyncio
async def test_evaluate_rules_success(rule_engine, time_based_rule, rate_limit_rule):
    """Test successful rule evaluation."""
    # Setup
    rule_engine.rules = {
        "rule1": time_based_rule,
        "rule2": rate_limit_rule
    }
    rule_engine._evaluate_rule = AsyncMock(return_value=True)
    
    # Execute
    results = await rule_engine.evaluate_rules(
        context={},
        rule_types={RuleType.TIME_BASED, RuleType.RATE_LIMIT}
    )
    
    # Verify
    assert len(results) == 2
    assert all(results.values())
    assert rule_engine.metrics.increment.call_count == 2

@pytest.mark.asyncio
async def test_evaluate_rules_filtered(rule_engine, time_based_rule, rate_limit_rule):
    """Test rule evaluation with type filtering."""
    # Setup
    rule_engine.rules = {
        "rule1": time_based_rule,
        "rule2": rate_limit_rule
    }
    rule_engine._evaluate_rule = AsyncMock(return_value=True)
    
    # Execute
    results = await rule_engine.evaluate_rules(
        context={},
        rule_types={RuleType.TIME_BASED}
    )
    
    # Verify
    assert len(results) == 1
    assert "rule1" in results

@pytest.mark.asyncio
async def test_evaluate_rules_priority_order(rule_engine, time_based_rule, rate_limit_rule):
    """Test rules are evaluated in priority order."""
    # Setup
    time_based_rule.priority = 1
    rate_limit_rule.priority = 2  # Higher priority
    rule_engine.rules = {
        "rule1": time_based_rule,
        "rule2": rate_limit_rule
    }
    
    evaluated_rules = []
    async def mock_evaluate(rule, context):
        evaluated_rules.append(rule.type)
        return True
    
    rule_engine._evaluate_rule = mock_evaluate
    
    # Execute
    await rule_engine.evaluate_rules(context={})
    
    # Verify
    assert evaluated_rules[0] == RuleType.RATE_LIMIT  # Higher priority evaluated first
    assert evaluated_rules[1] == RuleType.TIME_BASED

@pytest.mark.asyncio
async def test_evaluate_rules_inactive_rules(rule_engine, time_based_rule):
    """Test inactive rules are skipped."""
    # Setup
    time_based_rule.status = PolicyStatus.DISABLED
    rule_engine.rules = {"rule1": time_based_rule}
    rule_engine._evaluate_rule = AsyncMock(return_value=True)
    
    # Execute
    results = await rule_engine.evaluate_rules(context={})
    
    # Verify
    assert len(results) == 0
    rule_engine._evaluate_rule.assert_not_called()

@pytest.mark.asyncio
async def test_evaluate_rules_error_handling(rule_engine, time_based_rule):
    """Test error handling during rule evaluation."""
    # Setup
    rule_engine.rules = {"rule1": time_based_rule}
    rule_engine._evaluate_rule = AsyncMock(side_effect=Exception("Evaluation error"))
    
    # Execute and verify
    with pytest.raises(AuthError, match="Rule evaluation failed"):
        await rule_engine.evaluate_rules(context={})

@pytest.mark.asyncio
async def test_evaluate_rule_unknown_type(rule_engine):
    """Test handling of unknown rule types."""
    # Setup
    unknown_rule = EnforcementRule(
        type=RuleType.COMPLIANCE,  # No implementation for this type
        policy_type=PolicyType.ACCESS
    )
    
    # Execute
    result = await rule_engine._evaluate_rule(unknown_rule, {})
    
    # Verify
    assert result is False 