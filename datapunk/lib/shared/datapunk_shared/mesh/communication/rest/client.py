from typing import Optional, Dict, Any, Union, AsyncIterator
import aiohttp
import asyncio
from dataclasses import dataclass
from ...routing.retry import RetryPolicy
from ...routing.circuit import CircuitBreaker
from ...security.validation import SecurityContext, SecurityPolicy
from ...security.mtls import MTLSConfig
import ssl
import json
from ...monitoring import MetricsCollector
import time
import uuid

"""
REST Client Implementation for Datapunk Service Mesh

This module provides a robust REST client with built-in support for:
- Service mesh integration (discovery, health checks, circuit breaking)
- Security (MTLS, token management)
- Monitoring (metrics, tracing)
- Resilience (retry policies, connection pooling)

The client is designed to be used within the Datapunk ecosystem for secure
and reliable service-to-service communication, particularly between core
services like Lake, Stream, and Nexus Gateway.

TODO: Implement adaptive rate limiting based on service health metrics
TODO: Add support for custom serialization formats beyond JSON
FIXME: Improve error handling for partial responses in streaming mode
"""

@dataclass
class RestClientConfig:
    """
    Configuration for REST client with mesh integration support.
    
    NOTE: When using MTLS, ensure certificates are properly rotated and validated
    against the service mesh CA. See security/mtls.py for implementation details.
    """
    base_url: str
    timeout: float = 30.0  # Default timeout aligned with mesh requirements
    max_connections: int = 100  # Sized for typical service-to-service communication
    mtls_config: Optional[MTLSConfig] = None  # Required for mesh authentication
    security_policy: Optional[SecurityPolicy] = None  # Service-level access control
    retry_policy: Optional[RetryPolicy] = None  # Mesh-aware retry handling
    circuit_breaker: Optional[CircuitBreaker] = None  # Service protection
    default_headers: Optional[Dict[str, str]] = None  # Common request headers
    metrics_collector: Optional[MetricsCollector] = None  # For Prometheus integration
    trace_requests: bool = True  # OpenTelemetry tracing support
    request_logging: bool = True  # Detailed request logging for troubleshooting

class RestClient:
    """
    Async REST client with full service mesh integration.
    
    This client implements the Datapunk mesh communication patterns:
    - Secure by default with MTLS support
    - Circuit breaking for service protection
    - Retry policies for transient failures
    - Metrics collection for monitoring
    - Request tracing for debugging
    
    Example:
        async with RestClient(config) as client:
            response = await client.get("health")
            is_healthy = response.get("status") == "healthy"
    """
    def __init__(self, config: RestClientConfig):
        self.config = config
        self.session = None
        self._security_context = None
        
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def connect(self):
        """Initialize client session with configuration"""
        if self.session:
            return

        # Configure SSL context if MTLS is enabled
        ssl_context = None
        if self.config.mtls_config:
            ssl_context = ssl.create_default_context(
                purpose=ssl.Purpose.CLIENT_AUTH,
                cafile=self.config.mtls_config.ca_cert
            )
            ssl_context.load_cert_chain(
                certfile=self.config.mtls_config.certificate,
                keyfile=self.config.mtls_config.private_key
            )

        # Configure connection parameters
        conn = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=self.config.max_connections
        )

        # Create client session
        self.session = aiohttp.ClientSession(
            base_url=self.config.base_url,
            connector=conn,
            headers=self.config.default_headers or {},
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )

    async def close(self):
        """Close client session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _trace_request(
        self,
        method: str,
        path: str,
        start_time: float,
        status: int,
        error: Optional[str] = None
    ):
        """
        Record request metrics and tracing information for monitoring.
        
        Integrates with Prometheus for metrics collection and Jaeger for
        distributed tracing. See sys-arch.mmd for observability stack details.
        
        NOTE: High cardinality tags should be avoided to prevent metric explosion
        """
        if not self.config.metrics_collector:
            return

        duration = time.time() - start_time
        
        # Record basic metrics
        await self.config.metrics_collector.timing(
            "rest.client.request.duration",
            duration,
            tags={
                "method": method,
                "path": path,
                "status": status
            }
        )
        
        await self.config.metrics_collector.increment(
            "rest.client.request.count",
            tags={
                "method": method,
                "path": path,
                "status": status,
                "success": str(200 <= status < 300)
            }
        )
        
        if error:
            await self.config.metrics_collector.increment(
                "rest.client.request.error",
                tags={
                    "method": method,
                    "path": path,
                    "error": error
                }
            )

    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracing"""
        return str(uuid.uuid4())

    async def request(
        self,
        method: str,
        path: str,
        data: Optional[Union[Dict, str, bytes]] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict:
        """
        Make HTTP request with full mesh integration support.
        
        Implements the core request flow with:
        1. Circuit breaker protection
        2. Retry policy application
        3. Metrics collection
        4. Error handling
        
        FIXME: Add support for request context propagation
        TODO: Implement request prioritization
        """
        if not self.session:
            await self.connect()

        # Prepare request
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        request_headers = {**(self.config.default_headers or {}), **(headers or {})}

        # Serialize data if needed
        if isinstance(data, dict):
            data = json.dumps(data)
            request_headers["Content-Type"] = "application/json"

        async def _execute_request():
            async with self.session.request(
                method=method,
                url=url,
                data=data,
                params=params,
                headers=request_headers,
                timeout=timeout or self.config.timeout
            ) as response:
                # Handle different response types
                content_type = response.headers.get("Content-Type", "")
                
                if "application/json" in content_type:
                    result = await response.json()
                elif "text/" in content_type:
                    result = await response.text()
                else:
                    result = await response.read()

                # Raise for error status
                response.raise_for_status()
                
                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "data": result
                }

        # Apply circuit breaker and retry policy
        if self.config.circuit_breaker:
            _execute_request = self.config.circuit_breaker.execute(_execute_request)
            
        if self.config.retry_policy:
            _execute_request = self.config.retry_policy.execute(_execute_request)

        try:
            return await _execute_request()
        except aiohttp.ClientError as e:
            raise RestClientError(f"Request failed: {str(e)}")

    # Convenience methods for common HTTP methods
    async def get(self, path: str, **kwargs) -> Dict:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Dict:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Dict:
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Dict:
        return await self.request("DELETE", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> Dict:
        return await self.request("PATCH", path, **kwargs)

    async def get(
        self,
        path: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict:
        """Make GET request"""
        return await self.request("GET", path, params=params, headers=headers, timeout=timeout)

    async def post(
        self,
        path: str,
        data: Optional[Union[Dict, str, bytes]] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict:
        """Make POST request"""
        return await self.request("POST", path, data=data, params=params, headers=headers, timeout=timeout)

    async def put(
        self,
        path: str,
        data: Optional[Union[Dict, str, bytes]] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict:
        """Make PUT request"""
        return await self.request("PUT", path, data=data, params=params, headers=headers, timeout=timeout)

    async def delete(
        self,
        path: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict:
        """Make DELETE request"""
        return await self.request("DELETE", path, params=params, headers=headers, timeout=timeout)

    async def patch(
        self,
        path: str,
        data: Optional[Union[Dict, str, bytes]] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict:
        """Make PATCH request"""
        return await self.request("PATCH", path, data=data, params=params, headers=headers, timeout=timeout)

    async def head(
        self,
        path: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict:
        """Make HEAD request"""
        return await self.request("HEAD", path, params=params, headers=headers, timeout=timeout)

    async def options(
        self,
        path: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[float] = None
    ) -> Dict:
        """Make OPTIONS request"""
        return await self.request("OPTIONS", path, params=params, headers=headers, timeout=timeout)

    async def health_check(self) -> bool:
        """Check service health"""
        try:
            response = await self.get("health", timeout=5.0)
            return response.get("status") == "healthy"
        except Exception:
            return False

    def set_security_context(self, context: SecurityContext):
        """Set security context for requests"""
        self._security_context = context
        if context.token:
            self.session.headers["Authorization"] = f"Bearer {context.token}"

    async def stream(
        self,
        method: str,
        path: str,
        data: Optional[Union[Dict, str, bytes]] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        chunk_size: int = 8192
    ) -> AsyncIterator[bytes]:
        """
        Stream response data with backpressure support.
        
        Designed for large data transfers between services, particularly
        for Lake Service data ingestion and Stream Service real-time feeds.
        
        NOTE: chunk_size should be tuned based on network conditions and
        memory constraints. Default aligned with typical network buffer sizes.
        """
        if not self.session:
            await self.connect()

        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        request_headers = {**(self.config.default_headers or {}), **(headers or {})}

        if isinstance(data, dict):
            data = json.dumps(data)
            request_headers["Content-Type"] = "application/json"

        async def _execute_stream():
            async with self.session.request(
                method=method,
                url=url,
                data=data,
                params=params,
                headers=request_headers,
                chunked=True
            ) as response:
                response.raise_for_status()
                async for chunk in response.content.iter_chunked(chunk_size):
                    yield chunk

        # Apply circuit breaker if configured
        if self.config.circuit_breaker:
            _execute_stream = self.config.circuit_breaker.wrap(_execute_stream)

        try:
            async for chunk in _execute_stream():
                yield chunk
        except aiohttp.ClientError as e:
            raise RestClientError(f"Stream failed: {str(e)}")

    async def websocket_connect(
        self,
        path: str,
        headers: Optional[Dict] = None
    ) -> aiohttp.ClientWebSocketResponse:
        """Establish WebSocket connection"""
        if not self.session:
            await self.connect()

        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        request_headers = {**(self.config.default_headers or {}), **(headers or {})}

        try:
            return await self.session.ws_connect(
                url,
                headers=request_headers,
                heartbeat=30.0
            )
        except aiohttp.ClientError as e:
            raise RestClientError(f"WebSocket connection failed: {str(e)}")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        if not self.config.metrics_collector:
            return {}

        return {
            "total_requests": await self.config.metrics_collector.get_count(
                "rest.client.request.count"
            ),
            "total_errors": await self.config.metrics_collector.get_count(
                "rest.client.request.error"
            ),
            "average_duration": await self.config.metrics_collector.get_average(
                "rest.client.request.duration"
            )
        }

class RestClientError(Exception):
    """Base class for REST client errors"""
    pass 