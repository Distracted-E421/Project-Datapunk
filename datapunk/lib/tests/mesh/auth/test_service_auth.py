import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import jwt
from datapunk_shared.mesh.auth import (
    ServiceAuth,
    AuthConfig,
    ServiceCredentials,
    AuthToken,
    AuthError
)

@pytest.fixture
def auth_config():
    return AuthConfig(
        token_expiry=3600,  # 1 hour
        refresh_window=300,  # 5 minutes
        max_token_refresh=3,
        token_issuer="mesh-auth"
    )

@pytest.fixture
def service_auth(auth_config):
    return ServiceAuth(config=auth_config)

@pytest.fixture
def sample_credentials():
    return ServiceCredentials(
        service_id="service1",
        service_key="secret123",
        roles=["read", "write"],
        metadata={"environment": "prod"}
    )

@pytest.mark.asyncio
async def test_auth_initialization(service_auth, auth_config):
    assert service_auth.config == auth_config
    assert not service_auth.is_initialized
    assert len(service_auth.registered_services) == 0

@pytest.mark.asyncio
async def test_service_registration(service_auth, sample_credentials):
    await service_auth.register_service(sample_credentials)
    
    assert sample_credentials.service_id in service_auth.registered_services
    assert await service_auth.is_service_registered(sample_credentials.service_id)

@pytest.mark.asyncio
async def test_token_generation(service_auth, sample_credentials):
    await service_auth.register_service(sample_credentials)
    
    token = await service_auth.generate_token(
        sample_credentials.service_id,
        sample_credentials.service_key
    )
    
    assert token is not None
    assert isinstance(token, AuthToken)
    assert token.service_id == sample_credentials.service_id

@pytest.mark.asyncio
async def test_token_validation(service_auth, sample_credentials):
    await service_auth.register_service(sample_credentials)
    
    token = await service_auth.generate_token(
        sample_credentials.service_id,
        sample_credentials.service_key
    )
    
    is_valid = await service_auth.validate_token(token.token_string)
    assert is_valid

@pytest.mark.asyncio
async def test_token_refresh(service_auth, sample_credentials):
    await service_auth.register_service(sample_credentials)
    
    # Generate initial token
    token = await service_auth.generate_token(
        sample_credentials.service_id,
        sample_credentials.service_key
    )
    
    # Refresh token
    new_token = await service_auth.refresh_token(token.token_string)
    
    assert new_token is not None
    assert new_token.token_string != token.token_string
    assert new_token.refresh_count == token.refresh_count + 1

@pytest.mark.asyncio
async def test_token_expiration(service_auth, sample_credentials):
    # Configure short expiry for testing
    service_auth.config.token_expiry = 1  # 1 second
    
    await service_auth.register_service(sample_credentials)
    token = await service_auth.generate_token(
        sample_credentials.service_id,
        sample_credentials.service_key
    )
    
    # Wait for token to expire
    await asyncio.sleep(1.1)
    
    is_valid = await service_auth.validate_token(token.token_string)
    assert not is_valid

@pytest.mark.asyncio
async def test_service_to_service_auth(service_auth):
    # Register two services
    service1 = ServiceCredentials(
        service_id="service1",
        service_key="key1",
        roles=["read"]
    )
    service2 = ServiceCredentials(
        service_id="service2",
        service_key="key2",
        roles=["write"]
    )
    
    await service_auth.register_service(service1)
    await service_auth.register_service(service2)
    
    # Generate token for service1
    token = await service_auth.generate_token(
        service1.service_id,
        service1.service_key
    )
    
    # Verify service1 can access service2
    can_access = await service_auth.check_service_access(
        token.token_string,
        target_service="service2",
        required_roles=["read"]
    )
    assert can_access

@pytest.mark.asyncio
async def test_credential_rotation(service_auth, sample_credentials):
    await service_auth.register_service(sample_credentials)
    
    # Generate new credentials
    new_credentials = await service_auth.rotate_credentials(
        sample_credentials.service_id
    )
    
    assert new_credentials.service_key != sample_credentials.service_key
    
    # Old credentials should no longer work
    with pytest.raises(AuthError):
        await service_auth.generate_token(
            sample_credentials.service_id,
            sample_credentials.service_key
        )

@pytest.mark.asyncio
async def test_token_revocation(service_auth, sample_credentials):
    await service_auth.register_service(sample_credentials)
    
    token = await service_auth.generate_token(
        sample_credentials.service_id,
        sample_credentials.service_key
    )
    
    # Revoke token
    await service_auth.revoke_token(token.token_string)
    
    is_valid = await service_auth.validate_token(token.token_string)
    assert not is_valid

@pytest.mark.asyncio
async def test_auth_metrics_collection(service_auth, sample_credentials):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        await service_auth.register_service(sample_credentials)
        token = await service_auth.generate_token(
            sample_credentials.service_id,
            sample_credentials.service_key
        )
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_concurrent_token_validation(service_auth, sample_credentials):
    await service_auth.register_service(sample_credentials)
    
    # Generate multiple tokens
    tokens = []
    for _ in range(5):
        token = await service_auth.generate_token(
            sample_credentials.service_id,
            sample_credentials.service_key
        )
        tokens.append(token.token_string)
    
    # Validate tokens concurrently
    results = await asyncio.gather(*[
        service_auth.validate_token(token)
        for token in tokens
    ])
    
    assert all(results)

@pytest.mark.asyncio
async def test_token_claims_validation(service_auth, sample_credentials):
    await service_auth.register_service(sample_credentials)
    
    token = await service_auth.generate_token(
        sample_credentials.service_id,
        sample_credentials.service_key,
        additional_claims={"custom_claim": "value"}
    )
    
    decoded = await service_auth.decode_token(token.token_string)
    assert decoded["custom_claim"] == "value"

@pytest.mark.asyncio
async def test_auth_persistence(service_auth):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        await service_auth.save_state()
        mock_file.write.assert_called_once()
        
        await service_auth.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(service_auth):
    # Test with invalid credentials
    with pytest.raises(AuthError):
        await service_auth.generate_token(
            "nonexistent_service",
            "invalid_key"
        )

@pytest.mark.asyncio
async def test_token_refresh_limit(service_auth, sample_credentials):
    await service_auth.register_service(sample_credentials)
    
    token = await service_auth.generate_token(
        sample_credentials.service_id,
        sample_credentials.service_key
    )
    
    # Refresh token until limit
    current_token = token
    for _ in range(service_auth.config.max_token_refresh):
        current_token = await service_auth.refresh_token(
            current_token.token_string
        )
    
    # Next refresh should fail
    with pytest.raises(AuthError):
        await service_auth.refresh_token(current_token.token_string) 