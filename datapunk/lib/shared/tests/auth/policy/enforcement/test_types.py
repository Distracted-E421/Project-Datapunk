import pytest
from datetime import datetime
from datapunk_shared.auth.policy.enforcement.types import (
    EnforcementLevel, EnforcementAction, EnforcementContext, EnforcementResult
)

def test_enforcement_level_enum():
    """Test EnforcementLevel enum values."""
    assert EnforcementLevel.STRICT.value == "strict"
    assert EnforcementLevel.STANDARD.value == "standard"
    assert EnforcementLevel.PERMISSIVE.value == "permissive"
    assert EnforcementLevel.AUDIT.value == "audit"

def test_enforcement_action_enum():
    """Test EnforcementAction enum values."""
    assert EnforcementAction.BLOCK.value == "block"
    assert EnforcementAction.WARN.value == "warn"
    assert EnforcementAction.LOG.value == "log"
    assert EnforcementAction.NOTIFY.value == "notify"

def test_enforcement_context_creation():
    """Test EnforcementContext creation and properties."""
    now = datetime.utcnow()
    context = EnforcementContext(
        request_id="request-001",
        timestamp=now,
        client_ip="127.0.0.1",
        user_agent="test-agent",
        resource_path="/api/test",
        http_method="GET",
        headers={"Content-Type": "application/json"},
        query_params={"param1": "value1"},
        metadata={"test": "metadata"}
    )
    
    assert context.request_id == "request-001"
    assert context.timestamp == now
    assert context.client_ip == "127.0.0.1"
    assert context.user_agent == "test-agent"
    assert context.resource_path == "/api/test"
    assert context.http_method == "GET"
    assert context.headers == {"Content-Type": "application/json"}
    assert context.query_params == {"param1": "value1"}
    assert context.metadata == {"test": "metadata"}

def test_enforcement_context_optional_metadata():
    """Test EnforcementContext creation without optional metadata."""
    context = EnforcementContext(
        request_id="request-001",
        timestamp=datetime.utcnow(),
        client_ip="127.0.0.1",
        user_agent="test-agent",
        resource_path="/api/test",
        http_method="GET",
        headers={},
        query_params={}
    )
    
    assert context.metadata is None

def test_enforcement_result_creation():
    """Test EnforcementResult creation and properties."""
    now = datetime.utcnow()
    result = EnforcementResult(
        allowed=True,
        action=EnforcementAction.LOG,
        rules_evaluated=["rule1", "rule2"],
        rules_failed=[],
        context={"test": "context"},
        timestamp=now
    )
    
    assert result.allowed is True
    assert result.action == EnforcementAction.LOG
    assert result.rules_evaluated == ["rule1", "rule2"]
    assert result.rules_failed == []
    assert result.context == {"test": "context"}
    assert result.timestamp == now

def test_enforcement_result_with_failures():
    """Test EnforcementResult with failed rules."""
    result = EnforcementResult(
        allowed=False,
        action=EnforcementAction.BLOCK,
        rules_evaluated=["rule1", "rule2", "rule3"],
        rules_failed=["rule2"],
        context={"reason": "rule2 violation"},
        timestamp=datetime.utcnow()
    )
    
    assert result.allowed is False
    assert result.action == EnforcementAction.BLOCK
    assert len(result.rules_evaluated) == 3
    assert len(result.rules_failed) == 1
    assert "rule2" in result.rules_failed

def test_enforcement_context_headers_immutability():
    """Test that EnforcementContext headers can't be modified after creation."""
    headers = {"Content-Type": "application/json"}
    context = EnforcementContext(
        request_id="request-001",
        timestamp=datetime.utcnow(),
        client_ip="127.0.0.1",
        user_agent="test-agent",
        resource_path="/api/test",
        http_method="GET",
        headers=headers,
        query_params={}
    )
    
    # Modify original headers
    headers["New-Header"] = "value"
    
    # Verify context headers weren't modified
    assert "New-Header" not in context.headers

def test_enforcement_context_query_params_immutability():
    """Test that EnforcementContext query parameters can't be modified after creation."""
    params = {"param1": "value1"}
    context = EnforcementContext(
        request_id="request-001",
        timestamp=datetime.utcnow(),
        client_ip="127.0.0.1",
        user_agent="test-agent",
        resource_path="/api/test",
        http_method="GET",
        headers={},
        query_params=params
    )
    
    # Modify original params
    params["param2"] = "value2"
    
    # Verify context params weren't modified
    assert "param2" not in context.query_params

def test_enforcement_result_rules_immutability():
    """Test that EnforcementResult rule lists can't be modified after creation."""
    evaluated = ["rule1", "rule2"]
    failed = ["rule1"]
    
    result = EnforcementResult(
        allowed=False,
        action=EnforcementAction.BLOCK,
        rules_evaluated=evaluated,
        rules_failed=failed,
        context={},
        timestamp=datetime.utcnow()
    )
    
    # Modify original lists
    evaluated.append("rule3")
    failed.append("rule2")
    
    # Verify result lists weren't modified
    assert "rule3" not in result.rules_evaluated
    assert "rule2" not in result.rules_failed

def test_enforcement_result_context_immutability():
    """Test that EnforcementResult context can't be modified after creation."""
    context = {"reason": "test"}
    result = EnforcementResult(
        allowed=True,
        action=EnforcementAction.LOG,
        rules_evaluated=[],
        rules_failed=[],
        context=context,
        timestamp=datetime.utcnow()
    )
    
    # Modify original context
    context["new_key"] = "value"
    
    # Verify result context wasn't modified
    assert "new_key" not in result.context 