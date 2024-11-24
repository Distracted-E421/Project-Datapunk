from typing import Any, Optional, Dict
import grpc
from google.protobuf import message
from ...routing.retry import RetryPolicy
from ...routing.circuit import CircuitBreaker

class GrpcClientConfig:
    def __init__(
        self,
        target: str,
        timeout: float = 10.0,
        use_ssl: bool = True,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        metadata: Optional[Dict[str, str]] = None
    ):
        self.target = target
        self.timeout = timeout
        self.use_ssl = use_ssl
        self.retry_policy = retry_policy or RetryPolicy()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.metadata = metadata or {}

class GrpcClient:
    def __init__(self, config: GrpcClientConfig):
        self.config = config
        self._channel = None
        self._stub = None

    async def connect(self):
        if self.config.use_ssl:
            credentials = grpc.ssl_channel_credentials()
            self._channel = grpc.aio.secure_channel(
                self.config.target, 
                credentials
            )
        else:
            self._channel = grpc.aio.insecure_channel(self.config.target)

    async def close(self):
        if self._channel:
            await self._channel.close()

    async def call(
        self, 
        method: str, 
        request: message.Message, 
        timeout: Optional[float] = None
    ) -> Any:
        if not self._channel:
            await self.connect()

        async def _execute_call():
            return await self.config.circuit_breaker.execute(
                self._make_call,
                method,
                request,
                timeout or self.config.timeout
            )

        return await self.config.retry_policy.execute(_execute_call)

    async def _make_call(
        self, 
        method: str, 
        request: message.Message, 
        timeout: float
    ) -> Any:
        try:
            metadata = [
                (k, v) for k, v in self.config.metadata.items()
            ]
            return await getattr(self._stub, method)(
                request=request,
                timeout=timeout,
                metadata=metadata
            )
        except grpc.RpcError as e:
            # Convert gRPC errors to our custom exceptions
            # This helps with retry policy decisions
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ServiceUnavailableError(str(e))
            elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                raise TimeoutError(str(e))
            raise

class ServiceUnavailableError(Exception):
    pass 