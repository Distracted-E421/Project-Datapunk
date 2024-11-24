from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio
import time
import logging
from enum import Enum
from .health_metrics import HealthMetrics
from .health_check_types import HealthCheckResult, HealthStatus

class HealthCheckType(Enum):
    HTTP = "http"
    TCP = "tcp"
    CUSTOM = "custom"
    GRPC = "grpc"

class HealthChecker:
    def __init__(
        self,
        check_interval: float = 5.0,
        timeout: float = 3.0,
        metrics_enabled: bool = True
    ):
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
        """Add a new health check"""
        self.checks[service_id] = {
            'type': check_type,
            'target': target,
            'custom_check': custom_check,
            'headers': headers or {}
        }
        
        if self._running:
            self._tasks[service_id] = asyncio.create_task(
                self._run_check_loop(service_id)
            )

    async def start(self) -> None:
        """Start health checking"""
        self._running = True
        for service_id in self.checks:
            self._tasks[service_id] = asyncio.create_task(
                self._run_check_loop(service_id)
            )

    async def stop(self) -> None:
        """Stop health checking"""
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    async def _run_check_loop(self, service_id: str) -> None:
        """Run continuous health check loop for a service"""
        while self._running:
            try:
                result = await self._perform_check(service_id)
                self.results[service_id] = result
                
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
        """Perform actual health check"""
        check = self.checks[service_id]
        start_time = time.time()
        
        try:
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