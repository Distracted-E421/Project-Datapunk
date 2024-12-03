import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.communication.rest import (
    RestClient,
    ClientConfig,
    RetryConfig,
    RestError,
    RequestContext
)

@pytest.fixture
def client_config():
    return ClientConfig(
        base_url="http://localhost:8080",
        timeout=5.0,
        max_retries=3,
        pool_size=10,
        keepalive_timeout=30
    )

@pytest.fixture
def retry_config():
    return RetryConfig(
        max_attempts=3,
        initial_backoff=0.1,
        max_backoff=1.0,
        backoff_multiplier=2.0,
        retryable_status_codes=[500, 502, 503, 504]
    )

@pytest.fixture
def rest_client(client_config, retry_config):
    return RestClient(
        config=client_config,
        retry_config=retry_config
    )

@pytest.mark.asyncio
async def test_client_initialization(rest_client, client_config):
    assert rest_client.config == client_config
    assert not rest_client.is_closed
    assert rest_client.base_url == "http://localhost:8080"

@pytest.mark.asyncio
async def test_request_execution(rest_client):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"message": "Success"}
        )
        mock_session.return_value.request = AsyncMock(
            return_value=mock_response
        )
        
        response = await rest_client.request(
            method="GET",
            path="/api/test",
            params={"key": "value"}
        )
        
        assert response["message"] == "Success"
        mock_session.return_value.request.assert_called_once()

@pytest.mark.asyncio
async def test_retry_mechanism(rest_client):
    with patch('aiohttp.ClientSession') as mock_session:
        # Mock responses: two failures followed by success
        mock_responses = [
            AsyncMock(status=503),
            AsyncMock(status=503),
            AsyncMock(
                status=200,
                json=AsyncMock(return_value={"message": "Success"})
            )
        ]
        mock_session.return_value.request = AsyncMock(
            side_effect=mock_responses
        )
        
        response = await rest_client.request(
            method="GET",
            path="/api/test"
        )
        
        assert response["message"] == "Success"
        assert mock_session.return_value.request.call_count == 3

@pytest.mark.asyncio
async def test_error_handling(rest_client):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json = AsyncMock(
            return_value={"error": "Bad Request"}
        )
        mock_session.return_value.request = AsyncMock(
            return_value=mock_response
        )
        
        with pytest.raises(RestError) as exc_info:
            await rest_client.request(
                method="GET",
                path="/api/test"
            )
        
        assert exc_info.value.status == 400
        assert "Bad Request" in str(exc_info.value)

@pytest.mark.asyncio
async def test_request_timeout(rest_client):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value.request = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        
        with pytest.raises(RestError) as exc_info:
            await rest_client.request(
                method="GET",
                path="/api/test",
                timeout=1.0
            )
        
        assert "timeout" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_connection_pooling(rest_client):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"message": "Success"}
        )
        mock_session.return_value.request = AsyncMock(
            return_value=mock_response
        )
        
        # Make concurrent requests
        requests = [
            rest_client.request(
                method="GET",
                path="/api/test"
            )
            for _ in range(5)
        ]
        
        responses = await asyncio.gather(*requests)
        assert len(responses) == 5
        assert all(r["message"] == "Success" for r in responses)

@pytest.mark.asyncio
async def test_request_context(rest_client):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"message": "Success"}
        )
        mock_session.return_value.request = AsyncMock(
            return_value=mock_response
        )
        
        context = RequestContext(
            timeout=2.0,
            retry_attempts=2,
            headers={"Custom-Header": "Value"}
        )
        
        await rest_client.request(
            method="GET",
            path="/api/test",
            context=context
        )
        
        call_args = mock_session.return_value.request.call_args
        assert call_args.kwargs["timeout"] == 2.0
        assert call_args.kwargs["headers"]["Custom-Header"] == "Value"

@pytest.mark.asyncio
async def test_request_middleware(rest_client):
    middleware_calls = []
    
    @rest_client.middleware
    async def test_middleware(request, next_handler):
        middleware_calls.append("before")
        response = await next_handler(request)
        middleware_calls.append("after")
        return response
    
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"message": "Success"}
        )
        mock_session.return_value.request = AsyncMock(
            return_value=mock_response
        )
        
        await rest_client.request(
            method="GET",
            path="/api/test"
        )
        
        assert middleware_calls == ["before", "after"]

@pytest.mark.asyncio
async def test_request_compression(rest_client):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"message": "Success"}
        )
        mock_session.return_value.request = AsyncMock(
            return_value=mock_response
        )
        
        # Enable compression
        rest_client.config.compression_enabled = True
        
        await rest_client.request(
            method="POST",
            path="/api/test",
            data={"large": "x" * 1000}
        )
        
        call_args = mock_session.return_value.request.call_args
        assert "compress" in call_args.kwargs
        assert call_args.kwargs["compress"]

@pytest.mark.asyncio
async def test_request_metrics(rest_client):
    with patch('aiohttp.ClientSession') as mock_session:
        with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={"message": "Success"}
            )
            mock_session.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            await rest_client.request(
                method="GET",
                path="/api/test"
            )
            
            mock_collector.return_value.record_counter.assert_called()
            mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_circuit_breaker_integration(rest_client):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_responses = [
            AsyncMock(status=503),  # Failure
            AsyncMock(status=503),  # Failure
            AsyncMock(status=503),  # Failure - should open circuit
            AsyncMock(
                status=200,
                json=AsyncMock(return_value={"message": "Success"})
            )
        ]
        mock_session.return_value.request = AsyncMock(
            side_effect=mock_responses
        )
        
        # Configure circuit breaker
        rest_client.config.circuit_breaker_enabled = True
        rest_client.config.failure_threshold = 3
        
        # First three requests should fail
        for _ in range(3):
            with pytest.raises(RestError):
                await rest_client.request(
                    method="GET",
                    path="/api/test"
                )
        
        # Fourth request should be rejected by circuit breaker
        with pytest.raises(RestError) as exc_info:
            await rest_client.request(
                method="GET",
                path="/api/test"
            )
        
        assert "circuit breaker" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_graceful_shutdown(rest_client):
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session_instance = AsyncMock()
        mock_session.return_value = mock_session_instance
        
        # Start some requests
        active_requests = [
            asyncio.create_task(
                rest_client.request(
                    method="GET",
                    path="/api/test"
                )
            )
            for _ in range(3)
        ]
        
        # Initiate shutdown
        await rest_client.close(grace=2.0)
        
        mock_session_instance.close.assert_called_once()
        assert rest_client.is_closed