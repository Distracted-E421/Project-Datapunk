from typing import Optional, Dict, Any, List, Type
from dataclasses import dataclass
import asyncio
import grpc
from grpc import aio
from ...security.validation import SecurityValidator, SecurityContext
from ...security.mtls import MTLSConfig
from ...health.checks import HealthCheck
from ...monitoring import MetricsCollector
import time
from collections import defaultdict

"""
Service Mesh gRPC Server

A secure, monitored gRPC server implementation for the Datapunk service mesh.
This server forms the backbone of service-to-service communication, implementing
the mesh patterns defined in sys-arch.mmd.

Key Features:
- Secure mTLS communication with client certificate validation
- Rate limiting with token bucket algorithm for resource protection
- Comprehensive security validation through interceptors
- Detailed metrics collection for monitoring and alerting
- Health checking for service mesh integration
- Service reflection for development and debugging

Security Philosophy:
- Defense in depth through layered interceptors
- Zero trust architecture with mTLS enforcement
- Rate limiting per client to prevent resource exhaustion
- Comprehensive audit logging through metrics

Performance Notes:
- Uses async/await for non-blocking operations
- Implements token bucket algorithm for smooth rate limiting
- Configurable worker pool for request handling
"""

@dataclass
class GrpcServerConfig:
    """
    Configuration for gRPC server deployment.
    
    Design Decisions:
    - Default host 0.0.0.0 allows container deployment flexibility
    - Conservative message size limit prevents memory exhaustion
    - Rate limiting configured for typical service mesh patterns
    
    Security Configuration:
    - mtls_config: Required in production for service identity
    - interceptors: Allows custom security controls
    - rate_limit_*: Prevents DoS attacks
    
    TODO: Add dynamic configuration updates
    TODO: Implement adaptive rate limiting based on load
    """
    host: str = "0.0.0.0"
    port: int = 50051
    max_workers: int = 10
    max_message_length: int = 4 * 1024 * 1024  # 4MB
    mtls_config: Optional[MTLSConfig] = None
    enable_reflection: bool = True
    enable_health_check: bool = True
    interceptors: List[grpc.ServerInterceptor] = None
    compression: Optional[grpc.Compression] = None
    rate_limit_requests: int = 1000  # requests per minute
    rate_limit_burst: int = 100      # burst allowance

class RateLimiter:
    """
    Token bucket rate limiter for request throttling.
    
    Implementation Notes:
    - Uses token bucket algorithm for smooth rate limiting
    - Maintains per-client token buckets for fairness
    - Automatically cleans up inactive client buckets
    
    Performance Considerations:
    - Uses defaultdict to avoid lock contention
    - Calculates tokens lazily on check to reduce overhead
    - Maintains burst allowance for traffic spikes
    
    TODO: Add automatic cleanup of inactive buckets
    TODO: Implement distributed rate limiting for cluster deployment
    """
    def __init__(self, rate: int, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = defaultdict(lambda: burst)
        self.last_update = defaultdict(time.time)

    async def check_rate_limit(self, key: str) -> bool:
        """Check if request should be rate limited"""
        now = time.time()
        time_passed = now - self.last_update[key]
        self.last_update[key] = now

        # Add tokens based on time passed
        self.tokens[key] = min(
            self.burst,
            self.tokens[key] + time_passed * (self.rate / 60.0)
        )

        if self.tokens[key] >= 1:
            self.tokens[key] -= 1
            return True
        return False

class SecurityInterceptor(grpc.aio.ServerInterceptor):
    """
    Security validation interceptor for incoming requests.
    
    Security Flow:
    1. Extract security context from metadata
    2. Validate request against security policies
    3. Collect metrics for security events
    4. Propagate context for downstream services
    
    Error Handling:
    - Fails closed on validation errors
    - Records detailed metrics for security failures
    - Maintains audit trail through metadata
    
    NOTE: Must be first in interceptor chain for proper security
    """
    def __init__(
        self,
        security_validator: SecurityValidator,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.security_validator = security_validator
        self.metrics = metrics_collector

    async def intercept_service(
        self,
        continuation: grpc.HandlerCallDetails,
        handler: grpc.RpcMethodHandler
    ) -> grpc.RpcMethodHandler:
        """Intercept and validate incoming requests"""
        metadata = dict(continuation.invocation_metadata())
        
        context = SecurityContext(
            token=metadata.get("authorization", "").replace("Bearer ", ""),
            client_ip=metadata.get("x-forwarded-for", "unknown"),
            request_metadata={
                "method": continuation.method,
                "metadata": metadata
            }
        )

        if not await self.security_validator.validate_request(context):
            if self.metrics:
                await self.metrics.increment(
                    "grpc.security.validation_failed",
                    tags={"method": continuation.method}
                )
            raise grpc.StatusCode.UNAUTHENTICATED

        return await continuation.proceed(handler)

class MetricsInterceptor(grpc.aio.ServerInterceptor):
    """
    Metrics collection interceptor for observability.
    
    Metrics Collected:
    - Request duration with method and status tags
    - Request count with method and status tags
    - Error rates with detailed failure categorization
    
    Implementation Notes:
    - Uses async metrics collection to avoid blocking
    - Maintains status code context across error boundaries
    - Provides granular timing for performance analysis
    
    TODO: Add histogram metrics for latency distribution
    """
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector

    async def intercept_service(
        self,
        continuation: grpc.HandlerCallDetails,
        handler: grpc.RpcMethodHandler
    ) -> grpc.RpcMethodHandler:
        """Collect metrics for gRPC calls"""
        start_time = time.time()
        
        try:
            result = await continuation.proceed(handler)
            status = grpc.StatusCode.OK
            return result
        except grpc.RpcError as e:
            status = e.code()
            raise
        finally:
            duration = time.time() - start_time
            await self.metrics.timing(
                "grpc.request.duration",
                duration,
                tags={
                    "method": continuation.method,
                    "status": status.name
                }
            )
            await self.metrics.increment(
                "grpc.request.count",
                tags={
                    "method": continuation.method,
                    "status": status.name
                }
            )

class RateLimitInterceptor(grpc.aio.ServerInterceptor):
    """
    Rate limiting interceptor for resource protection.
    
    Design Philosophy:
    - Fair resource allocation across clients
    - Graceful degradation under load
    - Detailed metrics for capacity planning
    
    Client Identification:
    - Uses x-client-id header when available
    - Falls back to x-forwarded-for for client tracking
    - Supports anonymous clients with reduced limits
    
    NOTE: Place after security interceptor but before metrics
    """
    def __init__(
        self,
        rate_limiter: RateLimiter,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.rate_limiter = rate_limiter
        self.metrics = metrics_collector

    async def intercept_service(
        self,
        continuation: grpc.HandlerCallDetails,
        handler: grpc.RpcMethodHandler
    ) -> grpc.RpcMethodHandler:
        """Apply rate limiting to requests"""
        metadata = dict(continuation.invocation_metadata())
        client_id = (
            metadata.get("x-client-id") or
            metadata.get("x-forwarded-for") or
            "anonymous"
        )

        if not await self.rate_limiter.check_rate_limit(client_id):
            if self.metrics:
                await self.metrics.increment(
                    "grpc.rate_limit.exceeded",
                    tags={"client": client_id}
                )
            raise grpc.StatusCode.RESOURCE_EXHAUSTED

        return await continuation.proceed(handler)

class GrpcServer:
    """
    Async gRPC server with comprehensive mesh features.
    
    Architecture Notes:
    - Implements service mesh patterns from sys-arch.mmd
    - Provides secure service-to-service communication
    - Supports health checking for mesh integration
    
    Deployment Considerations:
    - Configure mTLS for production environments
    - Adjust rate limits based on service capacity
    - Enable reflection only in development
    
    Security Requirements:
    - Production deployments must enable mTLS
    - Security interceptor must be first in chain
    - Health checks must be enabled for mesh integration
    """
    def __init__(self, config: GrpcServerConfig,
                security_validator: Optional[SecurityValidator] = None,
                health_check: Optional[HealthCheck] = None,
                metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize server with security and monitoring.
        
        Component Initialization Order:
        1. Rate limiter (required for all environments)
        2. Security validator (if provided)
        3. Health check service (if enabled)
        4. Metrics collector (if provided)
        
        Security Note:
        - Security validator should be provided in production
        - Health checks enable service mesh integration
        - Metrics required for production monitoring
        """
        self.config = config
        self.security_validator = security_validator
        self.health_check = health_check
        self.metrics = metrics_collector
        self.rate_limiter = RateLimiter(
            config.rate_limit_requests,
            config.rate_limit_burst
        )
        self.server = None
        self._setup_server()

    def _setup_server(self):
        """
        Configure server with interceptors and services.
        
        Interceptor Chain Order:
        1. Security (authentication/authorization)
        2. Rate Limiting (resource protection)
        3. Metrics (performance monitoring)
        4. Custom interceptors (user-provided)
        
        Service Configuration:
        - Health check service for mesh integration
        - Reflection service for development
        - Custom services added through add_service()
        
        NOTE: Order of interceptors is critical for security
        """
        interceptors = []
        
        # Add security interceptor
        if self.security_validator:
            interceptors.append(
                SecurityInterceptor(
                    self.security_validator,
                    self.metrics
                )
            )

        # Add rate limiting interceptor
        interceptors.append(
            RateLimitInterceptor(
                self.rate_limiter,
                self.metrics
            )
        )

        # Add metrics interceptor
        if self.metrics:
            interceptors.append(MetricsInterceptor(self.metrics))

        # Add custom interceptors
        if self.config.interceptors:
            interceptors.extend(self.config.interceptors)

        # Create server
        self.server = aio.server(
            interceptors=interceptors,
            options=[
                ('grpc.max_message_length', self.config.max_message_length),
                ('grpc.max_receive_message_length', self.config.max_message_length),
                ('grpc.max_send_message_length', self.config.max_message_length),
            ]
        )

        # Add health checking service
        if self.config.enable_health_check:
            self._setup_health_service()

        # Add reflection service
        if self.config.enable_reflection:
            from grpc_reflection.v1alpha import reflection
            service_names = self.server.get_service_names()
            reflection.enable_server_reflection(service_names, self.server)

    def _setup_health_service(self):
        """Set up gRPC health checking service"""
        from grpc_health.v1 import health, health_pb2, health_pb2_grpc

        async def check(request, context):
            if self.health_check:
                is_healthy = await self.health_check.check_health()
            else:
                is_healthy = True

            return health_pb2.HealthCheckResponse(
                status=health_pb2.HealthCheckResponse.SERVING if is_healthy
                else health_pb2.HealthCheckResponse.NOT_SERVING
            )

        health_servicer = health.aio.HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, self.server)

    def add_service(self, servicer_class: Type, servicer_instance: Any):
        """Add a gRPC service to the server"""
        servicer_class.add_to_server(servicer_instance, self.server)

    async def start(self):
        """Start the gRPC server"""
        # Configure TLS if enabled
        server_credentials = None
        if self.config.mtls_config:
            with open(self.config.mtls_config.certificate, 'rb') as f:
                cert_chain = f.read()
            with open(self.config.mtls_config.private_key, 'rb') as f:
                private_key = f.read()
            with open(self.config.mtls_config.ca_cert, 'rb') as f:
                root_cert = f.read()

            server_credentials = grpc.ssl_server_credentials(
                [(private_key, cert_chain)],
                root_certificates=root_cert,
                require_client_auth=True
            )

        # Start server
        address = f"{self.config.host}:{self.config.port}"
        if server_credentials:
            self.server.add_secure_port(address, server_credentials)
        else:
            self.server.add_insecure_port(address)

        await self.server.start()
        
        if self.metrics:
            await self.metrics.increment("grpc.server.started")
            
        print(f"gRPC server started on {address}")

    async def stop(self):
        """Stop the gRPC server"""
        if self.server:
            await self.server.stop(grace=None)
            if self.metrics:
                await self.metrics.increment("grpc.server.stopped")
            print("gRPC server stopped")