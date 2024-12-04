from typing import Optional, Dict, Any, Callable, Awaitable, Type
from dataclasses import dataclass, field
from aiohttp import web
import asyncio
from ...security.validation import SecurityValidator, SecurityContext, SecurityPolicy
from ...security.mtls import MTLSConfig
from ...health.checks import HealthCheck
import ssl
import json
from aiohttp_cors import setup as cors_setup, ResourceOptions
import time
from collections import defaultdict

"""
REST Server Implementation for Datapunk Service Mesh

This module provides a secure and monitored REST server with:
- Service mesh integration (health checks, metrics)
- Multi-layer security (MTLS, token validation)
- Rate limiting and CORS support
- Request monitoring and metrics collection

The server is designed to expose service endpoints within the Datapunk
ecosystem while ensuring security, reliability, and observability.

TODO: Add support for graceful shutdown with connection draining
TODO: Implement request prioritization for critical endpoints
FIXME: Improve rate limiter memory usage for high-traffic scenarios
"""

@dataclass
class RestServerConfig:
    """
    Configuration for REST server with security and monitoring support.
    
    NOTE: CORS origins should be strictly limited in production environments.
    Default values are tuned for typical service mesh deployment scenarios.
    """
    host: str = "0.0.0.0"  # Listen on all interfaces for container deployment
    port: int = 8080  # Default port for service mesh routing
    mtls_config: Optional[MTLSConfig] = None  # Required for mesh authentication
    security_policy: Optional[SecurityPolicy] = None  # Request validation rules
    cors_origins: Optional[list[str]] = None  # Allowed CORS origins
    max_request_size: int = 1024 * 1024  # 1MB limit to prevent memory exhaustion
    request_timeout: float = 30.0  # Aligned with client default timeout
    rate_limit_requests: int = 100  # Requests per minute per client
    rate_limit_burst: int = 20  # Short-term burst allowance
    cors_settings: Dict[str, ResourceOptions] = field(default_factory=dict)

class RateLimiter:
    """
    Token bucket rate limiter for request throttling.
    
    Implements a distributed rate limiting strategy that:
    - Provides fair resource allocation across clients
    - Allows short-term burst handling
    - Prevents DoS attacks through traffic throttling
    
    NOTE: For high-traffic services, consider using Redis-based rate limiting
    TODO: Add support for dynamic rate adjustment based on server load
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

class RestServer:
    """
    Async REST server with comprehensive service mesh integration.
    
    Implements the core server patterns required by the Datapunk mesh:
    - Security-first design with MTLS and token validation
    - Health checking for service discovery
    - Metrics collection for monitoring
    - Rate limiting for service protection
    
    The middleware stack processes requests in the following order:
    1. Security first to reject unauthorized requests early
    2. Error handling to ensure consistent response format
    3. Rate limiting to protect server resources
    4. Metrics last to capture accurate request statistics
    """
    def __init__(
        self,
        config: RestServerConfig,
        security_validator: Optional[SecurityValidator] = None,
        health_check: Optional[HealthCheck] = None,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.security_validator = security_validator
        self.health_check = health_check
        self.metrics = metrics_collector
        self.rate_limiter = RateLimiter(
            config.rate_limit_requests,
            config.rate_limit_burst
        )
        self.app = web.Application(
            client_max_size=config.max_request_size
        )
        self._setup_middleware()
        self._setup_routes()
        self.runner = None
        self._setup_cors()

    def _setup_cors(self):
        """
        Configure CORS support for cross-origin requests.
        
        NOTE: In production, cors_origins should be explicitly set to prevent
        security vulnerabilities. Default permissive settings are for development only.
        """
        if self.config.cors_origins:
            cors = cors_setup(self.app, defaults={
                "*": ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                )
            })
            
            # Apply CORS to all routes
            for route in list(self.app.router.routes()):
                cors.add(route)

    def _setup_middleware(self):
        """
        Configure the middleware processing pipeline.
        
        The order of middleware is critical:
        1. Security first to reject unauthorized requests early
        2. Error handling to ensure consistent response format
        3. Rate limiting to protect server resources
        4. Metrics last to capture accurate request statistics
        
        FIXME: Add request context propagation for distributed tracing
        TODO: Consider adding request validation middleware
        """
        @web.middleware
        async def security_middleware(request: web.Request, handler: Callable):
            # Skip security for health check endpoint
            if request.path == "/health":
                return await handler(request)

            if self.security_validator:
                context = SecurityContext(
                    token=request.headers.get("Authorization", "").replace("Bearer ", ""),
                    client_ip=request.remote,
                    request_metadata={
                        "path": request.path,
                        "method": request.method,
                        "headers": dict(request.headers)
                    }
                )

                if not await self.security_validator.validate_request(context):
                    return web.json_response(
                        {"errors": context.validation_errors},
                        status=401
                    )

            return await handler(request)

        @web.middleware
        async def error_middleware(request: web.Request, handler: Callable):
            try:
                return await handler(request)
            except web.HTTPException as e:
                return web.json_response(
                    {"error": str(e)},
                    status=e.status
                )
            except Exception as e:
                return web.json_response(
                    {"error": "Internal server error"},
                    status=500
                )

        @web.middleware
        async def rate_limit_middleware(request: web.Request, handler: Callable):
            """Rate limiting middleware"""
            client_id = (
                request.headers.get("X-Client-ID") or 
                request.remote or 
                "anonymous"
            )
            
            if not await self.rate_limiter.check_rate_limit(client_id):
                return web.json_response(
                    {"error": "Rate limit exceeded"},
                    status=429
                )
            
            return await handler(request)

        @web.middleware
        async def metrics_middleware(request: web.Request, handler: Callable):
            """Request metrics middleware"""
            start_time = time.time()
            
            try:
                response = await handler(request)
                status = response.status
                return response
            except Exception as e:
                status = getattr(e, "status", 500)
                raise
            finally:
                if self.metrics:
                    duration = time.time() - start_time
                    await self.metrics.timing(
                        "rest.server.request.duration",
                        duration,
                        tags={
                            "method": request.method,
                            "path": request.path,
                            "status": status
                        }
                    )

        self.app.middlewares.extend([
            security_middleware,
            error_middleware,
            rate_limit_middleware,
            metrics_middleware
        ])

    def _setup_routes(self):
        """Set up basic routes"""
        self.app.router.add_get("/health", self._health_check_handler)

    async def _health_check_handler(self, request: web.Request) -> web.Response:
        """
        Handle health check requests from service mesh.
        
        Health checks are exempt from security middleware to prevent
        circular dependencies in the service mesh authentication.
        
        Returns 503 if health check fails to trigger service mesh failover.
        """
        if self.health_check:
            is_healthy = await self.health_check.check_health()
            status = 200 if is_healthy else 503
        else:
            is_healthy = True
            status = 200

        return web.json_response(
            {"status": "healthy" if is_healthy else "unhealthy"},
            status=status
        )

    def add_route(
        self,
        method: str,
        path: str,
        handler: Callable[[web.Request], Awaitable[web.Response]]
    ):
        """Add a route to the server"""
        self.app.router.add_route(method, path, handler)

    async def start(self):
        """
        Start the server with MTLS support if configured.
        
        SSL context is configured for mutual TLS when mtls_config is provided:
        - Requires client certificates
        - Validates against mesh CA
        - Uses server certificate for identification
        
        NOTE: Ensure certificates are properly rotated in production
        """
        # Configure SSL if MTLS is enabled
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
            ssl_context.verify_mode = ssl.CERT_REQUIRED

        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(
            self.runner,
            self.config.host,
            self.config.port,
            ssl_context=ssl_context
        )
        
        await site.start()
        
        if self.metrics:
            await self.metrics.increment("rest.server.started")
            
        print(f"REST server started on {self.config.host}:{self.config.port}")

    async def stop(self):
        """
        Stop the server and cleanup resources.
        
        TODO: Implement graceful shutdown:
        - Stop accepting new connections
        - Wait for existing requests to complete
        - Close idle connections
        - Cleanup resources
        """
        if self.runner:
            await self.runner.cleanup()
            if self.metrics:
                await self.metrics.increment("rest.server.stopped")
            print("REST server stopped") 