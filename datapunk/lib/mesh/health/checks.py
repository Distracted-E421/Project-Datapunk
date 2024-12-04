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

"""
Health Check Implementation for Datapunk Service Mesh

This module provides comprehensive health monitoring with:
- System resource monitoring (CPU, memory, disk)
- Service dependency checking
- Custom health check support
- Threshold-based status determination
- Metrics collection

Health checks are critical for maintaining mesh reliability and
enabling intelligent routing decisions.

TODO: Add network health monitoring
TODO: Implement predictive health analysis
FIXME: Improve resource usage during intensive checks
"""

class HealthStatus(Enum):
    """
    Service health states with routing implications.
    
    Status progression typically follows:
    HEALTHY -> DEGRADED -> UNHEALTHY
    
    UNKNOWN is used for initialization and check failures.
    NOTE: DEGRADED services remain in load balancing pools
    """
    HEALTHY = "healthy"     # Full service capability
    DEGRADED = "degraded"   # Limited but functional
    UNHEALTHY = "unhealthy" # Service failure
    UNKNOWN = "unknown"     # Status undetermined

@dataclass
class HealthCheckConfig:
    """
    Health check behavior configuration.
    
    Thresholds and intervals are tuned for:
    - Quick problem detection
    - Minimal false positives
    - Resource efficiency
    
    NOTE: failure_threshold should be > success_threshold
    TODO: Add support for check-specific thresholds
    """
    check_interval: float = 15.0  # Time between checks
    timeout: float = 5.0  # Individual check timeout
    failure_threshold: int = 3  # Failures before marking unhealthy
    success_threshold: int = 2  # Successes before marking healthy
    enable_system_checks: bool = True  # Monitor system resources
    cpu_threshold: float = 0.9  # CPU utilization limit
    memory_threshold: float = 0.9  # Memory utilization limit
    disk_threshold: float = 0.9  # Disk utilization limit
    enable_dependency_checks: bool = True  # Check dependencies
    dependency_timeout: float = 3.0  # Dependency check timeout

class HealthCheck:
    """
    Health monitoring manager for service mesh components.
    
    Core responsibilities:
    - Execute health checks
    - Track check history
    - Maintain status thresholds
    - Report metrics
    - Monitor dependencies
    
    Uses a sliding window approach for status changes to:
    - Prevent flapping
    - Handle transient failures
    - Provide status stability
    
    NOTE: All checks are executed asynchronously
    FIXME: Improve check scheduling for large numbers of checks
    """
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
        """
        Main health check execution loop.
        
        Implements check scheduling with:
        - Concurrent check execution
        - Error isolation
        - Metric recording
        - Status updates
        
        NOTE: Continues despite individual check failures
        TODO: Add check prioritization
        """
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
        """
        Execute all registered health checks.
        
        Check execution strategy:
        1. Run checks concurrently
        2. Isolate check failures
        3. Update check history
        4. Record metrics
        
        NOTE: Failed checks don't stop other checks
        FIXME: Add timeout for total check execution
        """
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
        """
        Update check status using threshold logic.
        
        Status changes require:
        - Multiple consecutive successes/failures
        - Threshold crossing
        - Valid check results
        
        This prevents status flapping from transient issues.
        NOTE: Thresholds can be tuned per environment
        """
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
        """
        Monitor CPU utilization with degradation detection.
        
        Uses a three-state model:
        1. HEALTHY: Below threshold
        2. DEGRADED: Slightly above threshold
        3. UNHEALTHY: Significantly above threshold
        
        NOTE: Requires psutil for accurate measurements
        TODO: Add CPU steal time detection for cloud environments
        """
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
        """
        Verify TCP port accessibility.
        
        Used for:
        - Dependency checking
        - Network connectivity verification
        - Service availability monitoring
        
        NOTE: Quick check without full protocol handshake
        TODO: Add protocol-specific health checks
        """
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