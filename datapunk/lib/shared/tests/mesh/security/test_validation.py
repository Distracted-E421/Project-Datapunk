import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.security import (
    SecurityValidator,
    ValidationConfig,
    ValidationRule,
    ValidationError,
    AccessPolicy
)

@pytest.fixture
def validation_config():
    return ValidationConfig(
        rules_refresh_interval=300,
        cache_ttl=60,
        max_cache_size=1000,
        strict_mode=True
    )

@pytest.fixture
def security_validator(validation_config):
    return SecurityValidator(config=validation_config)

@pytest.fixture
def sample_request():
    return {
        "method": "POST",
        "path": "/api/resource",
        "headers": {
            "Authorization": "Bearer token123",
            "Content-Type": "application/json"
        },
        "body": {"data": "test"}
    }

@pytest.fixture
def sample_token():
    return {
        "sub": "user123",
        "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        "scope": ["read", "write"],
        "iss": "auth-service"
    }

@pytest.mark.asyncio
async def test_validator_initialization(security_validator, validation_config):
    assert security_validator.config == validation_config
    assert not security_validator.is_initialized
    assert len(security_validator.rules) == 0

@pytest.mark.asyncio
async def test_request_validation(security_validator, sample_request):
    # Add validation rule
    rule = ValidationRule(
        path_pattern="/api/*",
        required_headers=["Authorization"],
        allowed_methods=["GET", "POST"],
        validate_body=True
    )
    security_validator.add_rule(rule)
    
    # Valid request
    result = await security_validator.validate_request(sample_request)
    assert result.is_valid
    assert not result.errors

@pytest.mark.asyncio
async def test_token_validation(security_validator, sample_token):
    with patch.object(security_validator, '_verify_token_signature') as mock_verify:
        mock_verify.return_value = True
        
        is_valid = await security_validator.validate_token(
            "token123",
            required_scopes=["read"]
        )
        assert is_valid

@pytest.mark.asyncio
async def test_access_control(security_validator):
    policy = AccessPolicy(
        resources=["/api/resource"],
        actions=["read", "write"],
        conditions={"ip_range": ["192.168.0.0/24"]}
    )
    
    security_validator.add_policy(policy)
    
    request = {
        "path": "/api/resource",
        "action": "read",
        "context": {"ip": "192.168.0.100"}
    }
    
    has_access = await security_validator.check_access(request)
    assert has_access

@pytest.mark.asyncio
async def test_validation_caching(security_validator, sample_request):
    with patch.object(security_validator, '_perform_validation') as mock_validate:
        mock_validate.return_value = True
        
        # First call should perform validation
        await security_validator.validate_request(sample_request)
        assert mock_validate.call_count == 1
        
        # Second call should use cache
        await security_validator.validate_request(sample_request)
        assert mock_validate.call_count == 1

@pytest.mark.asyncio
async def test_rule_refresh(security_validator):
    with patch.object(security_validator, '_load_rules') as mock_load:
        await security_validator.refresh_rules()
        mock_load.assert_called_once()

@pytest.mark.asyncio
async def test_validation_error_handling(security_validator):
    invalid_request = {
        "method": "INVALID",
        "path": "/api/resource"
    }
    
    result = await security_validator.validate_request(invalid_request)
    assert not result.is_valid
    assert len(result.errors) > 0

@pytest.mark.asyncio
async def test_custom_validation_rules(security_validator, sample_request):
    async def custom_validator(request):
        return request.get("headers", {}).get("X-Custom") == "valid"
    
    rule = ValidationRule(
        path_pattern="/api/*",
        custom_validators=[custom_validator]
    )
    security_validator.add_rule(rule)
    
    # Request without custom header
    result = await security_validator.validate_request(sample_request)
    assert not result.is_valid
    
    # Request with valid custom header
    sample_request["headers"]["X-Custom"] = "valid"
    result = await security_validator.validate_request(sample_request)
    assert result.is_valid

@pytest.mark.asyncio
async def test_rate_limiting(security_validator, sample_request):
    rule = ValidationRule(
        path_pattern="/api/*",
        rate_limit={"requests": 2, "period": 60}
    )
    security_validator.add_rule(rule)
    
    # First two requests should succeed
    assert (await security_validator.validate_request(sample_request)).is_valid
    assert (await security_validator.validate_request(sample_request)).is_valid
    
    # Third request should fail
    result = await security_validator.validate_request(sample_request)
    assert not result.is_valid
    assert "rate limit exceeded" in str(result.errors[0]).lower()

@pytest.mark.asyncio
async def test_validation_metrics(security_validator, sample_request):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        await security_validator.validate_request(sample_request)
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_validation_events(security_validator, sample_request):
    events = []
    
    def event_handler(event_type, request, result):
        events.append((event_type, request, result))
    
    security_validator.on_validation_event(event_handler)
    
    await security_validator.validate_request(sample_request)
    
    assert len(events) > 0
    assert events[0][0] == "validation_complete"

@pytest.mark.asyncio
async def test_concurrent_validation(security_validator, sample_request):
    rule = ValidationRule(
        path_pattern="/api/*",
        required_headers=["Authorization"]
    )
    security_validator.add_rule(rule)
    
    # Validate multiple requests concurrently
    requests = [sample_request.copy() for _ in range(5)]
    results = await asyncio.gather(*[
        security_validator.validate_request(req)
        for req in requests
    ])
    
    assert all(r.is_valid for r in results)

@pytest.mark.asyncio
async def test_validation_chain(security_validator, sample_request):
    # Create chain of validation rules
    rules = [
        ValidationRule(path_pattern="/api/*", required_headers=["Authorization"]),
        ValidationRule(path_pattern="/api/*", allowed_methods=["POST"]),
        ValidationRule(path_pattern="/api/*", validate_body=True)
    ]
    
    for rule in rules:
        security_validator.add_rule(rule)
    
    result = await security_validator.validate_request(sample_request)
    assert result.is_valid
    
    # Test chain breaking on first failure
    invalid_request = sample_request.copy()
    invalid_request["method"] = "DELETE"
    
    result = await security_validator.validate_request(invalid_request)
    assert not result.is_valid
    assert len(result.errors) == 1  # Should stop at first failure

@pytest.mark.asyncio
async def test_validation_context(security_validator, sample_request):
    context = {
        "environment": "production",
        "feature_flags": {"strict_validation": True}
    }
    
    rule = ValidationRule(
        path_pattern="/api/*",
        context_validators=[
            lambda ctx: ctx["environment"] == "production"
        ]
    )
    security_validator.add_rule(rule)
    
    result = await security_validator.validate_request(
        sample_request,
        context=context
    )
    assert result.is_valid 