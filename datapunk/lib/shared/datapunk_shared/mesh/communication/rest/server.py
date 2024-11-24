from typing import Optional, Dict, Any, Callable, Awaitable
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

@dataclass
class RestServerConfig:
    """Configuration for REST server"""
    host: str = "0.0.0.0"
    port: int = 8080
    mtls_config: Optional[MTLSConfig] = None
    security_policy: Optional[SecurityPolicy] = None
    cors_origins: Optional[list[str]] = None
    max_request_size: int = 1024 * 1024  # 1MB
    request_timeout: float = 30.0
    rate_limit_requests: int = 100  # requests per minute
    rate_limit_burst: int = 20      # burst allowance
    cors_settings: Dict[str, ResourceOptions] = field(default_factory=dict)

class RateLimiter:
    """Simple token bucket rate limiter"""
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
    """Async REST server with security and health checks"""
    def __init__(
        self,
        config: RestServerConfig,
        security_validator: Optional[SecurityValidator] = None,
        health_check: Optional[HealthCheck] = None
    ):
        self.config = config
        self.security_validator = security_validator
        self.health_check = health_check
        self.app = web.Application(
            client_max_size=config.max_request_size
        )
        self.rate_limiter = RateLimiter(
            config.rate_limit_requests,
            config.rate_limit_burst
        )
        self._setup_middleware()
        self._setup_routes()
        self.runner = None
        self._setup_cors()

    def _setup_cors(self):
        """Set up CORS support"""
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
        """Set up middleware stack"""
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
        """Handle health check requests"""
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
        """Start the server"""
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

        # Start the server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        site = web.TCPSite(
            self.runner,
            self.config.host,
            self.config.port,
            ssl_context=ssl_context
        )
        
        await site.start()
        print(f"REST server started on {self.config.host}:{self.config.port}")

    async def stop(self):
        """Stop the server"""
        if self.runner:
            await self.runner.cleanup()
            print("REST server stopped") 