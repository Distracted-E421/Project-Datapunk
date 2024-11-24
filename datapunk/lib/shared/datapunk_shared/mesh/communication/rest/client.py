from typing import Optional, Dict, Any, Union
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

@dataclass
class RestClientConfig:
    """Configuration for REST client"""
    base_url: str
    timeout: float = 30.0
    max_connections: int = 100
    mtls_config: Optional[MTLSConfig] = None
    security_policy: Optional[SecurityPolicy] = None
    retry_policy: Optional[RetryPolicy] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    default_headers: Optional[Dict[str, str]] = None
    metrics_collector: Optional[MetricsCollector] = None
    trace_requests: bool = True
    request_logging: bool = True

class RestClient:
    """Async REST client with security, retry, and circuit breaking"""
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
        """Record request metrics and tracing information"""
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
        """Make HTTP request with retry and circuit breaking"""
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

    def set_security_context(self, context: SecurityContext):
        """Set security context for subsequent requests"""
        self._security_context = context
        if context.token:
            self.config.default_headers = {
                **(self.config.default_headers or {}),
                "Authorization": f"Bearer {context.token}"
            }

class RestClientError(Exception):
    """Custom exception for REST client errors"""
    pass 