"""
Service Health Monitoring System

Part of the Datapunk service mesh infrastructure, this module provides real-time 
health monitoring for distributed services. It supports multiple protocols and custom
health checks with configurable intervals and timeouts.

Key Features:
- Multi-protocol support (HTTP, TCP, gRPC, Custom)
- Async health check execution
- Metrics collection integration
- Configurable check intervals and timeouts
- Extensible custom check support
"""

from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio
import time
import logging
from enum import Enum
from .health_metrics import HealthMetrics
from .health_check_types import HealthCheckResult, HealthStatus

class HealthCheckType(Enum):
    """Supported health check protocols and types.
    
    NOTE: When adding new check types, ensure corresponding check implementation
    is added to _perform_check method.
    """
    HTTP = "http"    # RESTful health endpoints
    TCP = "tcp"      # Raw TCP connection checks
    CUSTOM = "custom"  # User-defined health checks
    GRPC = "grpc"    # gRPC health probe support

class HealthChecker:
    """Asynchronous health checker for service mesh components.
    
    Manages multiple concurrent health checks across different protocols while
    maintaining check history and reporting metrics. Designed to integrate with
    the broader service mesh observability system.
    
    TODO: Add circuit breaker pattern for failing health checks
    TODO: Implement check result persistence for historical analysis
    """
    
    def __init__(
        self,
        check_interval: float = 5.0,
        timeout: float = 3.0,
        metrics_enabled: bool = True
    ):
        """
        Args:
            check_interval: Time between health checks in seconds
            timeout: Maximum time to wait for check response
            metrics_enabled: Whether to collect and report metrics
            
        NOTE: Default values chosen based on typical microservice response times.
        Adjust based on specific service SLAs and requirements.
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.checks: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, HealthCheckResult] = {}
        self.logger = logging.getLogger(__name__)
        self.metrics = HealthMetrics() if metrics_enabled else None
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}

    async def add_check(
        self,
        service_id: str,
        check_type: HealthCheckType,
        target: str,
        custom_check: Optional[Callable[[], Awaitable[bool]]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """Register a new health check for monitoring.
        
        IMPORTANT: If adding check while system is running, a new task is 
        automatically created and started. This ensures dynamic service 
        registration without system restart.
        
        Args:
            service_id: Unique identifier for the service
            check_type: Protocol/method to use for health check
            target: URL, host:port, or custom target identifier
            custom_check: Optional async function for custom health checks
            headers: Optional HTTP headers for REST health checks
        """
        self.checks[service_id] = {
            'type': check_type,
            'target': target,
            'custom_check': custom_check,
            'headers': headers or {}
        }
        
        # Dynamically start check if system is already running
        if self._running:
            self._tasks[service_id] = asyncio.create_task(
                self._run_check_loop(service_id)
            )

    async def start(self) -> None:
        """Start health checking system.
        
        Creates individual tasks for each registered health check to run
        concurrently. This allows independent monitoring of services without
        blocking or affecting other checks.
        """
        self._running = True
        for service_id in self.checks:
            self._tasks[service_id] = asyncio.create_task(
                self._run_check_loop(service_id)
            )

    async def stop(self) -> None:
        """Gracefully stop all health checks.
        
        Ensures proper cleanup of running tasks and resources. Uses gather with
        return_exceptions to prevent any single task failure from blocking shutdown.
        """
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    async def _run_check_loop(self, service_id: str) -> None:
        """Execute continuous health check loop for a specific service.
        
        IMPORTANT: This is a long-running coroutine that continues until explicitly
        stopped. Implements basic error handling and logging to ensure robustness.
        
        Args:
            service_id: Identifier of service to monitor
        """
        while self._running:
            try:
                result = await self._perform_check(service_id)
                self.results[service_id] = result
                
                # Record metrics if enabled for observability
                if self.metrics:
                    await self.metrics.record_health_check(
                        service_id,
                        result.status == HealthStatus.HEALTHY,
                        result.response_time
                    )

                if result.status != HealthStatus.HEALTHY:
                    self.logger.warning(f"Health check failed for {service_id}: {result.message}")
                
            except Exception as e:
                self.logger.error(f"Error in health check for {service_id}: {str(e)}")
                
            await asyncio.sleep(self.check_interval)

    async def _perform_check(self, service_id: str) -> HealthCheckResult:
        """Execute single health check based on configured type.
        
        TODO: Implement retry logic for transient failures
        TODO: Add support for custom timeout per check type
        
        Args:
            service_id: Service to check health for
            
        Returns:
            HealthCheckResult containing status and response time
        """
        check = self.checks[service_id]
        start_time = time.time()
        
        try:
            # Route to appropriate check implementation
            if check['type'] == HealthCheckType.HTTP:
                success = await self._http_check(check['target'], check['headers'])
            elif check['type'] == HealthCheckType.TCP:
                success = await self._tcp_check(check['target'])
            elif check['type'] == HealthCheckType.GRPC:
                success = await self._grpc_check(check['target'])
            elif check['type'] == HealthCheckType.CUSTOM and check['custom_check']:
                success = await check['custom_check']()
            else:
                raise ValueError(f"Invalid check type: {check['type']}")

            response_time = time.time() - start_time
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY if success else HealthStatus.UNHEALTHY,
                response_time=response_time,
                message="OK" if success else "Check failed"
            )

        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=str(e)
            ) 