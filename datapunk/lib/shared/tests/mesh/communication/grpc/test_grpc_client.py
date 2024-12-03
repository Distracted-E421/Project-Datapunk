import pytest
import asyncio
import grpc
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.communication.grpc import (
    GrpcClient,
    ClientConfig,
    RetryConfig,
    GrpcError,
    ConnectionState
)

@pytest.fixture
def client_config():
    return ClientConfig(
        target="localhost:50051",
        timeout=5.0,
        max_message_length=4 * 1024 * 1024,  # 4MB
        enable_retry=True,
        use_tls=False
    )

@pytest.fixture
def retry_config():
    return RetryConfig(
        max_attempts=3,
        initial_backoff=0.1,
        max_backoff=1.0,
        backoff_multiplier=2.0,
        retryable_status_codes=[
            grpc.StatusCode.UNAVAILABLE,
            grpc.StatusCode.DEADLINE_EXCEEDED
        ]
    )

@pytest.fixture
def grpc_client(client_config, retry_config):
    return GrpcClient(
        config=client_config,
        retry_config=retry_config
    )

@pytest.mark.asyncio
async def test_client_initialization(grpc_client, client_config):
    assert grpc_client.config == client_config
    assert grpc_client.state == ConnectionState.DISCONNECTED
    assert not grpc_client.is_connected

@pytest.mark.asyncio
async def test_connection_management(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        await grpc_client.connect()
        assert grpc_client.state == ConnectionState.CONNECTED
        assert grpc_client.is_connected
        
        await grpc_client.disconnect()
        assert grpc_client.state == ConnectionState.DISCONNECTED
        assert not grpc_client.is_connected

@pytest.mark.asyncio
async def test_unary_request(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_stub = AsyncMock()
        mock_method = AsyncMock()
        mock_method.return_value = {"message": "Success"}
        mock_stub.__getattr__.return_value = mock_method
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        await grpc_client.connect()
        grpc_client._stub = mock_stub
        
        response = await grpc_client.call(
            method="TestMethod",
            request={"data": "test"}
        )
        
        assert response["message"] == "Success"
        mock_method.assert_called_once()

@pytest.mark.asyncio
async def test_streaming_request(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_stub = AsyncMock()
        mock_stream = AsyncMock()
        
        async def mock_stream_response():
            for i in range(3):
                yield {"message": f"Response {i}"}
        
        mock_stream.__aiter__.return_value = mock_stream_response()
        mock_stub.__getattr__.return_value = mock_stream
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        await grpc_client.connect()
        grpc_client._stub = mock_stub
        
        responses = []
        async for response in grpc_client.stream(
            method="TestStreamMethod",
            request_iterator=({"data": f"item{i}"} for i in range(3))
        ):
            responses.append(response)
        
        assert len(responses) == 3
        assert all("Response" in r["message"] for r in responses)

@pytest.mark.asyncio
async def test_retry_mechanism(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_stub = AsyncMock()
        mock_method = AsyncMock()
        mock_method.side_effect = [
            grpc.aio.AioRpcError(
                code=grpc.StatusCode.UNAVAILABLE,
                details="Service unavailable"
            ),
            {"message": "Success"}
        ]
        mock_stub.__getattr__.return_value = mock_method
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        await grpc_client.connect()
        grpc_client._stub = mock_stub
        
        response = await grpc_client.call(
            method="TestMethod",
            request={"data": "test"}
        )
        
        assert response["message"] == "Success"
        assert mock_method.call_count == 2

@pytest.mark.asyncio
async def test_connection_recovery(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        # Simulate connection failure and recovery
        mock_channel_instance.get_state.side_effect = [
            grpc.ChannelConnectivity.TRANSIENT_FAILURE,
            grpc.ChannelConnectivity.READY
        ]
        
        await grpc_client.connect()
        
        # Trigger connection check
        await grpc_client.check_connection()
        assert grpc_client.state == ConnectionState.CONNECTED

@pytest.mark.asyncio
async def test_error_handling(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_stub = AsyncMock()
        mock_method = AsyncMock()
        mock_method.side_effect = grpc.aio.AioRpcError(
            code=grpc.StatusCode.INVALID_ARGUMENT,
            details="Invalid request"
        )
        mock_stub.__getattr__.return_value = mock_method
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        await grpc_client.connect()
        grpc_client._stub = mock_stub
        
        with pytest.raises(GrpcError) as exc_info:
            await grpc_client.call(
                method="TestMethod",
                request={"data": "invalid"}
            )
        
        assert exc_info.value.code == grpc.StatusCode.INVALID_ARGUMENT

@pytest.mark.asyncio
async def test_metadata_handling(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_stub = AsyncMock()
        mock_method = AsyncMock()
        mock_method.return_value = {"message": "Success"}
        mock_stub.__getattr__.return_value = mock_method
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        await grpc_client.connect()
        grpc_client._stub = mock_stub
        
        metadata = {
            "authorization": "Bearer token123",
            "request-id": "req-123"
        }
        
        await grpc_client.call(
            method="TestMethod",
            request={"data": "test"},
            metadata=metadata
        )
        
        # Verify metadata was passed
        call_args = mock_method.call_args
        assert "metadata" in call_args.kwargs
        passed_metadata = dict(call_args.kwargs["metadata"])
        assert passed_metadata["authorization"] == "Bearer token123"

@pytest.mark.asyncio
async def test_timeout_handling(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_stub = AsyncMock()
        mock_method = AsyncMock()
        mock_method.side_effect = asyncio.TimeoutError()
        mock_stub.__getattr__.return_value = mock_method
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        await grpc_client.connect()
        grpc_client._stub = mock_stub
        
        with pytest.raises(GrpcError) as exc_info:
            await grpc_client.call(
                method="TestMethod",
                request={"data": "test"},
                timeout=1.0
            )
        
        assert exc_info.value.code == grpc.StatusCode.DEADLINE_EXCEEDED

@pytest.mark.asyncio
async def test_connection_pooling(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_channel_instances = [AsyncMock() for _ in range(3)]
        mock_channel.side_effect = mock_channel_instances
        
        # Create multiple connections
        channels = await asyncio.gather(*[
            grpc_client.get_channel()
            for _ in range(3)
        ])
        
        assert len(channels) == 3
        assert len(grpc_client._channel_pool) == 3

@pytest.mark.asyncio
async def test_load_balancing(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        # Configure load balancing policy
        grpc_client.config.load_balancing_policy = "round_robin"
        
        await grpc_client.connect()
        
        channel_args = mock_channel.call_args.kwargs
        assert "options" in channel_args
        assert any(
            opt[0] == "grpc.lb_policy_name" and opt[1] == "round_robin"
            for opt in channel_args["options"]
        )

@pytest.mark.asyncio
async def test_compression(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_stub = AsyncMock()
        mock_method = AsyncMock()
        mock_method.return_value = {"message": "Success"}
        mock_stub.__getattr__.return_value = mock_method
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        await grpc_client.connect()
        grpc_client._stub = mock_stub
        
        # Enable compression
        grpc_client.config.enable_compression = True
        
        await grpc_client.call(
            method="TestMethod",
            request={"data": "test"}
        )
        
        call_args = mock_method.call_args
        assert "compression" in call_args.kwargs

@pytest.mark.asyncio
async def test_keepalive(grpc_client):
    with patch('grpc.aio.insecure_channel') as mock_channel:
        mock_channel_instance = AsyncMock()
        mock_channel.return_value = mock_channel_instance
        
        # Configure keepalive
        grpc_client.config.keepalive_time_ms = 1000
        grpc_client.config.keepalive_timeout_ms = 500
        
        await grpc_client.connect()
        
        channel_args = mock_channel.call_args.kwargs
        assert "options" in channel_args
        options = dict(channel_args["options"])
        assert "grpc.keepalive_time_ms" in options
        assert "grpc.keepalive_timeout_ms" in options 