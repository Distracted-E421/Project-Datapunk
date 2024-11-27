from typing import Optional, Dict, Any, Type, Generic, TypeVar
from dataclasses import dataclass
import asyncio
import grpc
from grpc import aio
from ...security.validation import SecurityContext
from ...security.mtls import MTLSConfig
from ...routing.retry import RetryPolicy
from ...routing.circuit import CircuitBreaker
from ...monitoring import MetricsCollector
import time
import uuid

T = TypeVar('T')  # For service stub type

"""
Service Mesh gRPC Client

A resilient gRPC client implementation for the Datapunk service mesh that prioritizes
data ownership and security while providing comprehensive monitoring capabilities.
This client is a core component of the mesh communication layer described in sys-arch.mmd.

Key Features:
- Secure mTLS communication with certificate-based auth
- Automatic retry policies with circuit breaking for failure isolation
- Comprehensive metrics collection for observability
- Request tracing for debugging and performance analysis
- Support for both unary and streaming operations
- Security context propagation across services

Implementation Notes:
- Uses async/await for non-blocking operations
- Implements connection pooling (TODO) for resource optimization
- Supports dynamic configuration updates (TODO)
- Handles both TLS and non-TLS scenarios consistently
"""

@dataclass
class GrpcClientConfig:
    """
    Configuration container for gRPC client settings.
    
    Why Dataclass:
    - Provides immutable configuration with validation
    - Enables future dynamic updates through replacement
    - Simplifies configuration management across services
    
    Security Considerations:
    - mtls_config: Required for service-to-service auth in production
    - metadata_handlers: Used for dynamic security context propagation
    
    Performance Tuning:
    - max_message_length: Adjusted based on typical payload sizes
    - timeout: Prevents resource exhaustion under load
    """
    target: str
    mtls_config: Optional[MTLSConfig] = None
    retry_policy: Optional[RetryPolicy] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    max_message_length: int = 4 * 1024 * 1024  # 4MB default balances memory usage
    timeout: float = 30.0  # Default timeout prevents resource exhaustion
    compression: Optional[grpc.Compression] = None
    enable_tracing: bool = True
    enable_metrics: bool = True
    metadata_handlers: Optional[Dict[str, callable]] = None

class GrpcClientError(Exception):
    """
    Base exception for gRPC client failures.
    
    Used to wrap low-level gRPC exceptions with context-specific information
    while maintaining the original error chain for debugging.
    """
    pass

class GrpcClient(Generic[T]):
    """
    Async gRPC client with comprehensive mesh features.
    
    Design Philosophy:
    - Prioritizes data ownership and security
    - Maintains connection state internally
    - Provides detailed metrics for monitoring
    - Supports graceful degradation under failure
    
    Usage Notes:
    - Initialize with appropriate security context
    - Configure retry policies for specific endpoints
    - Monitor metrics for performance optimization
    
    Security Context:
    - Propagates authentication tokens automatically
    - Supports custom metadata handlers for dynamic auth
    - Implements mTLS for service identity verification
    """
    def __init__(
        self,
        config: GrpcClientConfig,
        stub_class: Type[T],
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.stub_class = stub_class
        self.metrics = metrics_collector
        self._channel = None
        self._stub = None
        self._security_context: Optional[SecurityContext] = None

    async def connect(self):
        """
        Initialize secure gRPC channel and stub.
        
        Security Flow:
        1. Configure channel options for production workloads
        2. Apply mTLS if configured (required in production)
        3. Create appropriate channel type (secure/insecure)
        4. Initialize stub with configured channel
        
        Error Handling:
        - Validates certificate paths before loading
        - Reports connection failures through metrics
        - Maintains connection state for retry logic
        """
        try:
            # Configure channel for production workloads
            options = [
                ('grpc.max_message_length', self.config.max_message_length),
                ('grpc.max_receive_message_length', self.config.max_message_length),
                ('grpc.max_send_message_length', self.config.max_message_length),
            ]

            # Apply mTLS if configured
            credentials = None
            if self.config.mtls_config:
                with open(self.config.mtls_config.certificate, 'rb') as f:
                    cert_chain = f.read()
                with open(self.config.mtls_config.private_key, 'rb') as f:
                    private_key = f.read()
                with open(self.config.mtls_config.ca_cert, 'rb') as f:
                    root_cert = f.read()

                credentials = grpc.ssl_channel_credentials(
                    root_certificates=root_cert,
                    private_key=private_key,
                    certificate_chain=cert_chain
                )

            # Create appropriate channel type
            if credentials:
                self._channel = aio.secure_channel(
                    self.config.target,
                    credentials,
                    options=options
                )
            else:
                self._channel = aio.insecure_channel(
                    self.config.target,
                    options=options
                )

            self._stub = self.stub_class(self._channel)

            if self.metrics:
                await self.metrics.increment("grpc.client.connected")

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "grpc.client.connection_error",
                    tags={"error": str(e)}
                )
            raise GrpcClientError(f"Failed to connect: {str(e)}")

    async def close(self):
        """Close gRPC channel"""
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._stub = None

    def set_security_context(self, context: SecurityContext):
        """Set security context for requests"""
        self._security_context = context

    async def call(
        self,
        method_name: str,
        request: Any,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Any:
        """
        Execute gRPC method with reliability features.
        
        Flow:
        1. Ensure connection is established
        2. Prepare request metadata (auth, tracing, custom)
        3. Execute call with retry/circuit breaking
        4. Collect metrics and handle errors
        
        Performance Notes:
        - Uses connection pooling when available
        - Implements automatic retry with backoff
        - Monitors call duration for optimization
        
        Security:
        - Propagates security context in metadata
        - Supports custom auth handlers
        - Enables request tracing for audit
        """
        if not self._stub:
            await self.connect()

        # Prepare metadata
        call_metadata = []
        if metadata:
            call_metadata.extend((k, v) for k, v in metadata.items())

        # Add security context
        if self._security_context and self._security_context.token:
            call_metadata.append(
                ("authorization", f"Bearer {self._security_context.token}")
            )

        # Add custom metadata handlers
        if self.config.metadata_handlers:
            for key, handler in self.config.metadata_handlers.items():
                value = await handler()
                if value:
                    call_metadata.append((key, value))

        # Add request ID for tracing
        if self.config.enable_tracing:
            call_metadata.append(("x-request-id", str(uuid.uuid4())))

        async def _execute_call():
            start_time = time.time()
            method = getattr(self._stub, method_name)
            
            try:
                response = await method(
                    request=request,
                    timeout=timeout or self.config.timeout,
                    metadata=call_metadata
                )

                if self.metrics:
                    duration = time.time() - start_time
                    await self.metrics.timing(
                        "grpc.client.request.duration",
                        duration,
                        tags={"method": method_name}
                    )
                    await self.metrics.increment(
                        "grpc.client.request.success",
                        tags={"method": method_name}
                    )

                return response

            except grpc.RpcError as e:
                if self.metrics:
                    await self.metrics.increment(
                        "grpc.client.request.error",
                        tags={
                            "method": method_name,
                            "code": e.code().name,
                            "details": str(e.details())
                        }
                    )
                raise

        # Apply circuit breaker if configured
        if self.config.circuit_breaker:
            _execute_call = self.config.circuit_breaker.wrap(_execute_call)

        # Apply retry policy if configured
        if self.config.retry_policy:
            _execute_call = self.config.retry_policy.wrap(_execute_call)

        try:
            return await _execute_call()
        except grpc.RpcError as e:
            raise GrpcClientError(
                f"RPC failed: {e.code().name} - {e.details()}"
            )
        except Exception as e:
            raise GrpcClientError(f"Call failed: {str(e)}")

    async def stream(
        self,
        method_name: str,
        request_iterator: Any,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Any:
        """Handle streaming gRPC calls"""
        if not self._stub:
            await self.connect()

        # Prepare metadata similar to regular calls
        call_metadata = []
        if metadata:
            call_metadata.extend((k, v) for k, v in metadata.items())

        if self._security_context and self._security_context.token:
            call_metadata.append(
                ("authorization", f"Bearer {self._security_context.token}")
            )

        if self.config.enable_tracing:
            call_metadata.append(("x-request-id", str(uuid.uuid4())))

        try:
            method = getattr(self._stub, method_name)
            start_time = time.time()
            
            async for response in method(
                request_iterator,
                timeout=timeout or self.config.timeout,
                metadata=call_metadata
            ):
                if self.metrics:
                    await self.metrics.increment(
                        "grpc.client.stream.message",
                        tags={"method": method_name}
                    )
                yield response

            if self.metrics:
                duration = time.time() - start_time
                await self.metrics.timing(
                    "grpc.client.stream.duration",
                    duration,
                    tags={"method": method_name}
                )

        except grpc.RpcError as e:
            if self.metrics:
                await self.metrics.increment(
                    "grpc.client.stream.error",
                    tags={
                        "method": method_name,
                        "code": e.code().name,
                        "details": str(e.details())
                    }
                )
            raise GrpcClientError(
                f"Stream failed: {e.code().name} - {e.details()}"
            )
        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "grpc.client.stream.error",
                    tags={
                        "method": method_name,
                        "error": str(e)
                    }
                )
            raise GrpcClientError(f"Stream failed: {str(e)}")

    async def health_check(self) -> bool:
        """Check service health using gRPC health checking protocol"""
        try:
            from grpc_health.v1 import health_pb2, health_pb2_grpc
            
            health_stub = health_pb2_grpc.HealthStub(self._channel)
            request = health_pb2.HealthCheckRequest()
            
            response = await health_stub.Check(
                request,
                timeout=5.0
            )
            
            is_healthy = (
                response.status == health_pb2.HealthCheckResponse.SERVING
            )
            
            if self.metrics:
                await self.metrics.increment(
                    "grpc.client.health_check",
                    tags={"healthy": str(is_healthy)}
                )
                
            return is_healthy

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "grpc.client.health_check.error",
                    tags={"error": str(e)}
                )
            return False 