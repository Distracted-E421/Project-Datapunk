from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import asyncio
import aiohttp
from datetime import datetime, timedelta
from enum import Enum
import psutil
import socket
from ..discovery.registry import ServiceRegistration
from ...monitoring import MetricsCollector

class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckConfig:
    """Configuration for health checks"""
    check_interval: float = 15.0  # seconds
    timeout: float = 5.0  # seconds
    failure_threshold: int = 3
    success_threshold: int = 2
    enable_system_checks: bool = True
    cpu_threshold: float = 0.9  # 90% utilization
    memory_threshold: float = 0.9  # 90% utilization
    disk_threshold: float = 0.9  # 90% utilization
    enable_dependency_checks: bool = True
    dependency_timeout: float = 3.0  # seconds

class HealthCheck:
    """Health check implementation"""
    def __init__(
        self,
        config: HealthCheckConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.metrics = metrics_collector
        self._checks: Dict[str, Callable] = {}
        self._check_results: Dict[str, Dict[str, Any]] = {}
        self._failure_counts: Dict[str, int] = {}
        self._success_counts: Dict[str, int] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._check_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start health check process"""
        self._running = True
        self._session = aiohttp.ClientSession()
        self._check_task = asyncio.create_task(self._check_loop())

        # Register system checks if enabled
        if self.config.enable_system_checks:
            self.register_check("system.cpu", self._check_cpu)
            self.register_check("system.memory", self._check_memory)
            self.register_check("system.disk", self._check_disk)

    async def stop(self):
        """Stop health check process"""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()

    def register_check(self, name: str, check: Callable):
        """Register a health check"""
        self._checks[name] = check
        self._failure_counts[name] = 0
        self._success_counts[name] = 0

    def unregister_check(self, name: str):
        """Unregister a health check"""
        self._checks.pop(name, None)
        self._failure_counts.pop(name, None)
        self._success_counts.pop(name, None)
        self._check_results.pop(name, None)

    async def check_health(self) -> bool:
        """Check overall system health"""
        results = await self._run_all_checks()
        return all(r.get("status") == HealthStatus.HEALTHY for r in results.values())

    async def check_url_health(self, url: str) -> bool:
        """Check health of a URL endpoint"""
        try:
            async with self._session.get(
                url,
                timeout=self.config.timeout
            ) as response:
                return 200 <= response.status < 300
        except Exception:
            return False

    async def check_instance_health(
        self,
        instance: ServiceRegistration
    ) -> bool:
        """Check health of a service instance"""
        if not instance.health_check_url:
            return True  # Assume healthy if no health check URL

        return await self.check_url_health(instance.health_check_url)

    async def _check_loop(self):
        """Main health check loop"""
        while self._running:
            try:
                await self._run_all_checks()
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "health.check.error",
                        tags={"error": str(e)}
                    )

    async def _run_all_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run all registered health checks"""
        results = {}
        for name, check in self._checks.items():
            try:
                result = await check()
                self._update_check_status(name, result)
                results[name] = result
                
                if self.metrics:
                    await self.metrics.gauge(
                        "health.check.status",
                        1 if result["status"] == HealthStatus.HEALTHY else 0,
                        tags={"check": name}
                    )
                    
            except Exception as e:
                results[name] = {
                    "status": HealthStatus.UNHEALTHY,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if self.metrics:
                    await self.metrics.increment(
                        "health.check.error",
                        tags={"check": name, "error": str(e)}
                    )

        self._check_results = results
        return results

    def _update_check_status(self, name: str, result: Dict[str, Any]):
        """Update check status based on thresholds"""
        if result["status"] == HealthStatus.HEALTHY:
            self._success_counts[name] += 1
            self._failure_counts[name] = 0
            if self._success_counts[name] >= self.config.success_threshold:
                result["status"] = HealthStatus.HEALTHY
        else:
            self._failure_counts[name] += 1
            self._success_counts[name] = 0
            if self._failure_counts[name] >= self.config.failure_threshold:
                result["status"] = HealthStatus.UNHEALTHY

    async def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU utilization"""
        cpu_percent = psutil.cpu_percent(interval=1) / 100.0
        return {
            "status": (
                HealthStatus.HEALTHY
                if cpu_percent < self.config.cpu_threshold
                else HealthStatus.DEGRADED
                if cpu_percent < self.config.cpu_threshold * 1.1
                else HealthStatus.UNHEALTHY
            ),
            "value": cpu_percent,
            "threshold": self.config.cpu_threshold,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory utilization"""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent / 100.0
        return {
            "status": (
                HealthStatus.HEALTHY
                if memory_percent < self.config.memory_threshold
                else HealthStatus.DEGRADED
                if memory_percent < self.config.memory_threshold * 1.1
                else HealthStatus.UNHEALTHY
            ),
            "value": memory_percent,
            "threshold": self.config.memory_threshold,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _check_disk(self) -> Dict[str, Any]:
        """Check disk utilization"""
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent / 100.0
        return {
            "status": (
                HealthStatus.HEALTHY
                if disk_percent < self.config.disk_threshold
                else HealthStatus.DEGRADED
                if disk_percent < self.config.disk_threshold * 1.1
                else HealthStatus.UNHEALTHY
            ),
            "value": disk_percent,
            "threshold": self.config.disk_threshold,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def check_tcp_port(self, host: str, port: int) -> bool:
        """Check if TCP port is accessible"""
        try:
            _, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def get_health_stats(self) -> Dict[str, Any]:
        """Get health check statistics"""
        return {
            "total_checks": len(self._checks),
            "healthy_checks": sum(
                1 for r in self._check_results.values()
                if r.get("status") == HealthStatus.HEALTHY
            ),
            "degraded_checks": sum(
                1 for r in self._check_results.values()
                if r.get("status") == HealthStatus.DEGRADED
            ),
            "unhealthy_checks": sum(
                1 for r in self._check_results.values()
                if r.get("status") == HealthStatus.UNHEALTHY
            ),
            "last_check_results": self._check_results,
            "failure_counts": self._failure_counts.copy(),
            "success_counts": self._success_counts.copy()
        }