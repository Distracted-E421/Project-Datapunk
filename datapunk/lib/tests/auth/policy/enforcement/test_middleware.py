import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datapunk_shared.auth.policy.enforcement.middleware import PolicyEnforcementMiddleware
from datapunk_shared.auth.policy.enforcement.rules import RuleEngine, RuleType
from datapunk_shared.auth.policy.types import PolicyType

@pytest.fixture
def app():
    """Create a FastAPI application instance."""
    return FastAPI()

@pytest.fixture
def rule_engine():
    """Create a mock rule engine."""
    engine = Mock()
    engine.evaluate_rules = AsyncMock()
    return engine

@pytest.fixture
def metrics_client():
    """Create a mock metrics client."""
    client = Mock()
    client.increment = Mock()
    return client

@pytest.fixture
def middleware(app, rule_engine, metrics_client):
    """Create a PolicyEnforcementMiddleware instance."""
    return PolicyEnforcementMiddleware(app, rule_engine, metrics_client)

@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = Mock(spec=Request)
    request.method = "GET"
    request.url.path = "/test"
    request.headers = {}
    request.query_params = {}
    request.client = Mock()
    request.client.host = "127.0.0.1"
    request.state = Mock()
    request.state.policy_type = PolicyType.ACCESS
    return request

@pytest.fixture
def mock_response():
    """Create a mock response."""
    response = JSONResponse(content={})
    response.status_code = 200
    return response

@pytest.mark.asyncio
async def test_dispatch_success(middleware, mock_request, mock_response):
    """Test successful policy enforcement."""
    # Setup
    middleware.rule_engine.evaluate_rules.return_value = {
        "rule1": True,
        "rule2": True
    }
    async def mock_call_next(request):
        return mock_response
    
    # Execute
    response = await middleware.dispatch(mock_request, mock_call_next)
    
    # Verify
    assert response.status_code == 200
    middleware.rule_engine.evaluate_rules.assert_called_once()
    middleware.metrics.increment.assert_called()

@pytest.mark.asyncio
async def test_dispatch_failed_rules(middleware, mock_request):
    """Test policy enforcement with failed rules."""
    # Setup
    middleware.rule_engine.evaluate_rules.return_value = {
        "rule1": False,
        "rule2": True
    }
    async def mock_call_next(request):
        return JSONResponse(content={})
    
    # Execute and verify
    with pytest.raises(HTTPException) as exc_info:
        await middleware.dispatch(mock_request, mock_call_next)
    
    assert exc_info.value.status_code == 403
    assert "Policy rules failed" in exc_info.value.detail

@pytest.mark.asyncio
async def test_dispatch_unexpected_error(middleware, mock_request):
    """Test handling of unexpected errors during enforcement."""
    # Setup
    middleware.rule_engine.evaluate_rules.side_effect = Exception("Unexpected error")
    async def mock_call_next(request):
        return JSONResponse(content={})
    
    # Execute and verify
    with pytest.raises(HTTPException) as exc_info:
        await middleware.dispatch(mock_request, mock_call_next)
    
    assert exc_info.value.status_code == 500
    assert "Policy enforcement failed" in exc_info.value.detail

@pytest.mark.asyncio
async def test_dispatch_with_default_policy_type(middleware, mock_request):
    """Test policy enforcement with default policy type."""
    # Setup
    mock_request.state.policy_type = None
    middleware.rule_engine.evaluate_rules.return_value = {"rule1": True}
    async def mock_call_next(request):
        return JSONResponse(content={}, status_code=200)
    
    # Execute
    response = await middleware.dispatch(mock_request, mock_call_next)
    
    # Verify
    assert response.status_code == 200
    call_args = middleware.rule_engine.evaluate_rules.call_args[1]
    assert call_args["context"]["policy_type"] == PolicyType.ACCESS.value

@pytest.mark.asyncio
async def test_dispatch_rule_context(middleware, mock_request, mock_response):
    """Test context passed to rule engine."""
    # Setup
    middleware.rule_engine.evaluate_rules.return_value = {"rule1": True}
    async def mock_call_next(request):
        return mock_response
    
    # Execute
    await middleware.dispatch(mock_request, mock_call_next)
    
    # Verify
    call_args = middleware.rule_engine.evaluate_rules.call_args[1]
    context = call_args["context"]
    assert context["method"] == "GET"
    assert context["path"] == "/test"
    assert context["client_ip"] == "127.0.0.1"
    assert "timestamp" in context

@pytest.mark.asyncio
async def test_dispatch_rule_types(middleware, mock_request, mock_response):
    """Test rule types passed to rule engine."""
    # Setup
    middleware.rule_engine.evaluate_rules.return_value = {"rule1": True}
    async def mock_call_next(request):
        return mock_response
    
    # Execute
    await middleware.dispatch(mock_request, mock_call_next)
    
    # Verify
    call_args = middleware.rule_engine.evaluate_rules.call_args[1]
    rule_types = call_args["rule_types"]
    assert RuleType.TIME_BASED in rule_types
    assert RuleType.RATE_LIMIT in rule_types
    assert RuleType.GEO_LOCATION in rule_types

def test_update_metrics(middleware, mock_request, mock_response):
    """Test metrics update after policy enforcement."""
    # Setup
    rule_results = {
        "rule1": True,
        "rule2": False
    }
    
    # Execute
    middleware._update_metrics(mock_request, rule_results, mock_response)
    
    # Verify
    assert middleware.metrics.increment.call_count == 3  # One overall + two rules
    
    # Verify overall metrics
    overall_call = middleware.metrics.increment.call_args_list[0]
    assert overall_call[0][0] == "policy_enforcement_total"
    assert overall_call[0][1]["path"] == "/test"
    assert overall_call[0][1]["method"] == "GET"
    assert overall_call[0][1]["status"] == 200
    assert overall_call[0][1]["rules_passed"] == "false"
    
    # Verify rule-specific metrics
    rule1_call = middleware.metrics.increment.call_args_list[1]
    assert rule1_call[0][0] == "policy_rule_results"
    assert rule1_call[0][1]["rule_id"] == "rule1"
    assert rule1_call[0][1]["result"] == "true"
    
    rule2_call = middleware.metrics.increment.call_args_list[2]
    assert rule2_call[0][0] == "policy_rule_results"
    assert rule2_call[0][1]["rule_id"] == "rule2"
    assert rule2_call[0][1]["result"] == "false" 