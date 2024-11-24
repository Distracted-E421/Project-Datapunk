from typing import Optional, Dict, Any, List, Callable
import grpc
import asyncio
from datetime import datetime
from dataclasses import dataclass
from ...health.checks import HealthCheck, HealthStatus
from ...security.mtls import MTLSConfig  # Will implement this next
from concurrent.futures import ThreadPoolExecutor

@dataclass
class ServerMetrics:
    request_count: int = 0
    error_count: int = 0
    active_connections: int = 0
    last_request_time: Optional[datetime] = None
    average_response_time: float = 0.0

class GrpcServerConfig:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 50051,
        max_workers: int = 10,
        mtls_config: Optional[MTLSConfig] = None,
        interceptors: Optional[List[grpc.ServerInterceptor]] = None,
        health_check_interval: int = 30
    ):
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.mtls_config = mtls_config
        self.interceptors = interceptors or []
        self.health_check_interval = health_check_interval

class GrpcServer:
    def __init__(
        self, 
        config: GrpcServerConfig,
        servicer: Any  # The actual gRPC servicer implementation
    ):
        self.config = config
        self.servicer = servicer
        self.server = None
        self.metrics = ServerMetrics()
        self._health_check = HealthCheck(
            check_fn=self._check_health,
            interval_seconds=config.health_check_interval
        )
        self._executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """Start the gRPC server with all configured components"""
        try:
            # Create server with interceptors
            self.server = grpc.aio.server(
                interceptors=self.config.interceptors,
                executor=self._executor
            )

            # Add the service implementation
            service_name = self.servicer.__class__.__name__
            add_servicer_fn = getattr(
                self.servicer.__class__, f"add_{service_name}_to_server"
            )
            add_servicer_fn(self.servicer, self.server)

            # Configure security if MTLS is enabled
            if self.config.mtls_config:
                credentials = await self._setup_mtls_credentials()
                port = self.server.add_secure_port(
                    f"{self.config.host}:{self.config.port}",
                    credentials
                )
            else:
                port = self.server.add_insecure_port(
                    f"{self.config.host}:{self.config.port}"
                )

            # Start health checking
            asyncio.create_task(self._health_check.start_monitoring())

            # Start the server
            await self.server.start()
            
            print(f"gRPC server started on port {port}")
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()

        except Exception as e:
            print(f"Failed to start gRPC server: {e}")
            raise

    async def stop(self):
        """Gracefully shutdown the server"""
        if self.server:
            self._shutdown_event.set()
            await self.server.stop(grace=5)  # 5 second grace period
            self._executor.shutdown(wait=True)
            print("gRPC server stopped")

    def _update_metrics(self, start_time: datetime, error: bool = False):
        """Update server metrics after each request"""
        self.metrics.request_count += 1
        if error:
            self.metrics.error_count += 1
        
        self.metrics.last_request_time = datetime.now()
        
        # Update average response time
        duration = (datetime.now() - start_time).total_seconds()
        self.metrics.average_response_time = (
            (self.metrics.average_response_time * (self.metrics.request_count - 1) + duration)
            / self.metrics.request_count
        )

    async def _check_health(self) -> bool:
        """Health check implementation"""
        if not self.server:
            return False
            
        # Basic health criteria
        is_healthy = (
            self.server.is_running() and
            self.metrics.error_count / max(self.metrics.request_count, 1) < 0.5 and
            (datetime.now() - (self.metrics.last_request_time or datetime.now())).seconds < 300
        )
        
        return is_healthy

    async def _setup_mtls_credentials(self) -> grpc.ServerCredentials:
        """Set up mutual TLS credentials if configured"""
        if not self.config.mtls_config:
            raise ValueError("MTLS configuration is required for secure server")
            
        return grpc.ssl_server_credentials(
            [(
                self.config.mtls_config.private_key,
                self.config.mtls_config.certificate
            )],
            root_certificates=self.config.mtls_config.ca_cert,
            require_client_auth=True
        )

class MetricsInterceptor(grpc.ServerInterceptor):
    """Interceptor for collecting metrics on each request"""
    
    def __init__(self, server: GrpcServer):
        self.server = server

    async def intercept_service(
        self,
        continuation: Callable,
        handler_call_details: grpc.HandlerCallDetails
    ):
        start_time = datetime.now()
        self.server.metrics.active_connections += 1
        
        try:
            response = await continuation(handler_call_details)
            self.server._update_metrics(start_time)
            return response
        except Exception as e:
            self.server._update_metrics(start_time, error=True)
            raise
        finally:
            self.server.metrics.active_connections -= 1 