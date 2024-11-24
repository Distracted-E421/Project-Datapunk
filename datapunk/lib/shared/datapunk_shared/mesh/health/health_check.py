from typing import Dict, Any, List, Optional, Callable, Awaitable
import asyncio
import time
import structlog
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, Histogram
from ...utils.retry import with_retry, RetryConfig

logger = structlog.get_logger(__name__)

class HealthStatus:
    """Health status constants"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheck:
    """Health check implementation"""
    
    def __init__(
        self,
        name: str,
        check_interval: float = 30.0,
        timeout: float = 5.0,
        unhealthy_threshold: int = 3,
        healthy_threshold: int = 2
    ):
        self.name = name
        self.check_interval = check_interval
        self.timeout = timeout
        self.unhealthy_threshold = unhealthy_threshold
        self.healthy_threshold = healthy_threshold
        
        # State
        self.status = HealthStatus.UNHEALTHY
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_check_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.checks: List[Callable[[], Awaitable[bool]]] = []
        
        # Metrics
        self.check_counter = Counter(
            f'health_check_total_{name}',
            'Total number of health checks',
            ['status']
        )
        self.status_gauge = Gauge(
            f'health_check_status_{name}',
            'Current health check status (0=unhealthy, 1=degraded, 2=healthy)',
            ['service']
        )
        self.response_time = Histogram(
            f'health_check_response_time_{name}',
            'Health check response time',
            ['service']
        )
        
        self._update_metrics()
    
    def _update_metrics(self):
        """Update Prometheus metrics"""
        status_value = {
            HealthStatus.HEALTHY: 2,
            HealthStatus.DEGRADED: 1,
            HealthStatus.UNHEALTHY: 0
        }[self.status]
        
        self.status_gauge.labels(service=self.name).set(status_value)
    
    def add_check(self, check: Callable[[], Awaitable[bool]]):
        """Add health check function"""
        self.checks.append(check)
    
    async def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        start_time = time.time()
        results = []
        overall_status = HealthStatus.HEALTHY
        
        try:
            for check in self.checks:
                try:
                    is_healthy = await asyncio.wait_for(check(), self.timeout)
                    results.append({
                        "status": HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    if not is_healthy:
                        overall_status = HealthStatus.UNHEALTHY
                        self.consecutive_failures += 1
                        self.consecutive_successes = 0
                    
                except asyncio.TimeoutError:
                    results.append({
                        "status": HealthStatus.DEGRADED,
                        "error": "Check timed out",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    overall_status = HealthStatus.DEGRADED
                    
                except Exception as e:
                    results.append({
                        "status": HealthStatus.UNHEALTHY,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    overall_status = HealthStatus.UNHEALTHY
                    self.consecutive_failures += 1
                    self.consecutive_successes = 0
            
            # Update state based on thresholds
            if overall_status == HealthStatus.HEALTHY:
                self.consecutive_successes += 1
                if self.consecutive_successes >= self.healthy_threshold:
                    self.status = HealthStatus.HEALTHY
            
            elif self.consecutive_failures >= self.unhealthy_threshold:
                self.status = HealthStatus.UNHEALTHY
            
            # Update metrics
            self.check_counter.labels(status=overall_status).inc()
            self.response_time.labels(service=self.name).observe(time.time() - start_time)
            self._update_metrics()
            
            return {
                "service": self.name,
                "status": self.status,
                "checks": results,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "consecutive_failures": self.consecutive_failures,
                    "consecutive_successes": self.consecutive_successes,
                    "response_time": time.time() - start_time
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "service": self.name,
                "status": HealthStatus.UNHEALTHY,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

class HealthCheckCoordinator:
    """Coordinates health checks across services"""
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=15.0
        )
    
    def register_service(
        self,
        service_name: str,
        check_interval: float = 30.0,
        **kwargs: Any
    ) -> HealthCheck:
        """Register service for health checking"""
        health_check = HealthCheck(service_name, check_interval, **kwargs)
        self.health_checks[service_name] = health_check
        return health_check
    
    @with_retry()
    async def check_service(self, service_name: str) -> Dict[str, Any]:
        """Check specific service health"""
        health_check = self.health_checks.get(service_name)
        if not health_check:
            raise ValueError(f"Service {service_name} not registered")
            
        return await health_check.run_checks()
    
    async def check_all(self) -> Dict[str, Any]:
        """Check health of all services"""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for service_name, health_check in self.health_checks.items():
            try:
                result = await self.check_service(service_name)
                results[service_name] = result
                
                if result["status"] == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result["status"] == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
                    
            except Exception as e:
                results[service_name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                overall_status = HealthStatus.UNHEALTHY
        
        return {
            "status": overall_status,
            "services": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def start_monitoring(self):
        """Start periodic health monitoring"""
        while True:
            try:
                await self.check_all()
                await asyncio.sleep(min(
                    check.check_interval 
                    for check in self.health_checks.values()
                ))
            except Exception as e:
                logger.error(f"Health monitoring error: {str(e)}")
                await asyncio.sleep(5)  # Back off on error 