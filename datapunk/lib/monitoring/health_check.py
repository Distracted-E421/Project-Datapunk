from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None
    dependencies: Optional[Dict[str, 'HealthCheckResult']] = None

class HealthCheck:
    def __init__(self, name: str, check_func: Callable[[], HealthCheckResult], 
                 interval_seconds: int = 60, timeout_seconds: int = 10,
                 dependencies: List[str] = None, priority: int = 0):
        self.name = name
        self.check_func = check_func
        self.interval = timedelta(seconds=interval_seconds)
        self.timeout = timedelta(seconds=timeout_seconds)
        self.dependencies = dependencies or []
        self.priority = priority
        self.last_result: Optional[HealthCheckResult] = None
        self.last_check_time: Optional[datetime] = None

    async def execute(self) -> HealthCheckResult:
        try:
            result = await asyncio.wait_for(
                asyncio.coroutine(self.check_func)(), 
                timeout=self.timeout.total_seconds()
            )
            self.last_result = result
            self.last_check_time = datetime.now()
            return result
        except asyncio.TimeoutError:
            error_result = HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout.total_seconds()} seconds",
                timestamp=datetime.now()
            )
            self.last_result = error_result
            self.last_check_time = datetime.now()
            return error_result
        except Exception as e:
            error_result = HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e), "type": type(e).__name__}
            )
            self.last_result = error_result
            self.last_check_time = datetime.now()
            return error_result

class HealthCheckManager:
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self._running = False
        self._check_tasks: Dict[str, asyncio.Task] = {}

    def register_check(self, check: HealthCheck) -> None:
        """Register a new health check."""
        if check.name in self.checks:
            raise ValueError(f"Health check with name '{check.name}' already registered")
        
        # Validate dependencies
        for dep in check.dependencies:
            if dep not in self.checks:
                raise ValueError(f"Dependency '{dep}' not found for check '{check.name}'")
        
        self.checks[check.name] = check
        logger.info(f"Registered health check: {check.name}")

    def unregister_check(self, name: str) -> None:
        """Unregister a health check."""
        if name in self._check_tasks:
            self._check_tasks[name].cancel()
            del self._check_tasks[name]
        
        if name in self.checks:
            del self.checks[name]
            logger.info(f"Unregistered health check: {name}")

    async def _run_check_loop(self, check: HealthCheck) -> None:
        """Run a health check in a loop with its specified interval."""
        while self._running:
            try:
                await check.execute()
            except Exception as e:
                logger.error(f"Error running health check {check.name}: {e}")
            
            await asyncio.sleep(check.interval.total_seconds())

    async def start(self) -> None:
        """Start running all registered health checks."""
        if self._running:
            return

        self._running = True
        
        # Sort checks by priority to ensure dependencies run first
        sorted_checks = sorted(self.checks.values(), key=lambda x: x.priority)
        
        for check in sorted_checks:
            if check.name not in self._check_tasks:
                self._check_tasks[check.name] = asyncio.create_task(
                    self._run_check_loop(check)
                )

    async def stop(self) -> None:
        """Stop all running health checks."""
        self._running = False
        
        for task in self._check_tasks.values():
            task.cancel()
        
        if self._check_tasks:
            await asyncio.gather(*self._check_tasks.values(), return_exceptions=True)
        
        self._check_tasks.clear()

    def get_status(self) -> Dict[str, HealthCheckResult]:
        """Get the current status of all health checks."""
        return {name: check.last_result for name, check in self.checks.items()
                if check.last_result is not None}

    def get_check_status(self, name: str) -> Optional[HealthCheckResult]:
        """Get the status of a specific health check."""
        check = self.checks.get(name)
        return check.last_result if check else None

    def is_healthy(self) -> bool:
        """Check if all health checks are healthy."""
        statuses = self.get_status()
        return all(result.status == HealthStatus.HEALTHY for result in statuses.values())

    def get_unhealthy_checks(self) -> Dict[str, HealthCheckResult]:
        """Get all unhealthy checks."""
        return {name: result for name, result in self.get_status().items()
                if result.status != HealthStatus.HEALTHY} 