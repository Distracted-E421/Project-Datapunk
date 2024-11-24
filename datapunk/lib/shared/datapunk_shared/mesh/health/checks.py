from enum import Enum
from typing import Callable, Optional
import asyncio

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheck:
    def __init__(
        self, 
        check_fn: Callable[[], bool],
        interval_seconds: int = 30,
        timeout_seconds: int = 5
    ):
        self.check_fn = check_fn
        self.interval = interval_seconds
        self.timeout = timeout_seconds
        self.status = HealthStatus.UNHEALTHY
        
    async def start_monitoring(self):
        while True:
            try:
                result = await asyncio.wait_for(
                    self.check_fn(), 
                    timeout=self.timeout
                )
                self.status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
            except asyncio.TimeoutError:
                self.status = HealthStatus.DEGRADED
            except Exception:
                self.status = HealthStatus.UNHEALTHY
            
            await asyncio.sleep(self.interval) 