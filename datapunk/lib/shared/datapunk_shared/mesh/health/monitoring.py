from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from .checks import HealthCheck, HealthStatus
from ..discovery.registry import ServiceRegistry, ServiceRegistration
from ...monitoring import MetricsCollector
import psutil
import statistics

class MonitoringLevel(Enum):
    """Monitoring severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class HealthMetrics:
    """Health metrics data point"""
    service_id: str
    status: HealthStatus
    error_rate: float
    response_time: float
    memory_usage: float
    cpu_usage: float
    connections: int
    last_check: datetime
    level: MonitoringLevel

@dataclass
class MonitoringConfig:
    """Configuration for health monitoring"""
    check_interval: float = 15.0  # seconds
    metrics_retention: int = 24 * 60 * 60  # 24 hours in seconds
    error_threshold: float = 0.1  # 10% error rate
    response_time_threshold: float = 1.0  # 1 second
    memory_threshold: float = 0.9  # 90% usage
    cpu_threshold: float = 0.8  # 80% usage
    connection_threshold: int = 1000
    enable_alerts: bool = True
    alert_cooldown: int = 300  # 5 minutes between similar alerts

class HealthMonitor:
    """Monitors service health metrics"""
    def __init__(
        self,
        config: MonitoringConfig,
        health_check: HealthCheck,
        registry: ServiceRegistry,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.health_check = health_check
        self.registry = registry
        self.metrics = metrics_collector
        self._monitoring_task: Optional[asyncio.Task] = None
        self._metrics_history: Dict[str, List[HealthMetrics]] = {}
        self._last_alerts: Dict[str, datetime] = {}
        self._running = False

    async def start(self):
        """Start health monitoring"""
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop(self):
        """Stop health monitoring"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                await self._check_all_services()
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "health.monitoring.error",
                        tags={"error": str(e)}
                    )

    async def _check_all_services(self):
        """Check health of all registered services"""
        services = await self.registry.get_services()
        
        for service in services:
            try:
                metrics = await self._collect_service_metrics(service)
                await self._process_metrics(metrics)
                
                if self.config.enable_alerts:
                    await self._check_alerts(metrics)
                    
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "health.monitoring.service_error",
                        tags={
                            "service": service.id,
                            "error": str(e)
                        }
                    )

    async def _collect_service_metrics(
        self,
        service: ServiceRegistration
    ) -> HealthMetrics:
        """Collect health metrics for a service"""
        # Check basic health
        is_healthy = await self.health_check.check_instance_health(service)
        status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY

        # Get resource usage
        try:
            process = psutil.Process(service.pid) if hasattr(service, 'pid') else None
            if process:
                memory_usage = process.memory_percent() / 100.0
                cpu_usage = process.cpu_percent() / 100.0
                connections = len(process.connections())
            else:
                memory_usage = 0.0
                cpu_usage = 0.0
                connections = 0
        except Exception:
            memory_usage = 0.0
            cpu_usage = 0.0
            connections = 0

        # Calculate error rate and response time from history
        history = self._metrics_history.get(service.id, [])[-100:]  # Last 100 checks
        if history:
            error_rate = sum(1 for m in history if m.status == HealthStatus.UNHEALTHY) / len(history)
            response_time = statistics.mean(m.response_time for m in history)
        else:
            error_rate = 0.0
            response_time = 0.0

        # Determine monitoring level
        level = self._determine_level(
            error_rate,
            response_time,
            memory_usage,
            cpu_usage,
            connections
        )

        return HealthMetrics(
            service_id=service.id,
            status=status,
            error_rate=error_rate,
            response_time=response_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            connections=connections,
            last_check=datetime.utcnow(),
            level=level
        )

    def _determine_level(
        self,
        error_rate: float,
        response_time: float,
        memory_usage: float,
        cpu_usage: float,
        connections: int
    ) -> MonitoringLevel:
        """Determine monitoring level based on metrics"""
        if (
            error_rate > self.config.error_threshold * 2 or
            memory_usage > self.config.memory_threshold * 1.2 or
            cpu_usage > self.config.cpu_threshold * 1.2
        ):
            return MonitoringLevel.CRITICAL
            
        elif (
            error_rate > self.config.error_threshold or
            response_time > self.config.response_time_threshold * 2 or
            memory_usage > self.config.memory_threshold or
            cpu_usage > self.config.cpu_threshold or
            connections > self.config.connection_threshold
        ):
            return MonitoringLevel.ERROR
            
        elif (
            error_rate > self.config.error_threshold * 0.5 or
            response_time > self.config.response_time_threshold or
            memory_usage > self.config.memory_threshold * 0.8 or
            cpu_usage > self.config.cpu_threshold * 0.8 or
            connections > self.config.connection_threshold * 0.8
        ):
            return MonitoringLevel.WARNING
            
        return MonitoringLevel.INFO

    async def _process_metrics(self, metrics: HealthMetrics):
        """Process and store metrics"""
        service_id = metrics.service_id
        
        # Update metrics history
        if service_id not in self._metrics_history:
            self._metrics_history[service_id] = []
            
        self._metrics_history[service_id].append(metrics)
        
        # Clean up old metrics
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.config.metrics_retention)
        self._metrics_history[service_id] = [
            m for m in self._metrics_history[service_id]
            if m.last_check > cutoff_time
        ]
        
        # Record metrics
        if self.metrics:
            tags = {"service": service_id}
            
            await self.metrics.gauge(
                "health.service.error_rate",
                metrics.error_rate,
                tags=tags
            )
            await self.metrics.gauge(
                "health.service.response_time",
                metrics.response_time,
                tags=tags
            )
            await self.metrics.gauge(
                "health.service.memory_usage",
                metrics.memory_usage,
                tags=tags
            )
            await self.metrics.gauge(
                "health.service.cpu_usage",
                metrics.cpu_usage,
                tags=tags
            )
            await self.metrics.gauge(
                "health.service.connections",
                metrics.connections,
                tags=tags
            )

    async def _check_alerts(self, metrics: HealthMetrics):
        """Check if alerts should be triggered"""
        if metrics.level in (MonitoringLevel.ERROR, MonitoringLevel.CRITICAL):
            alert_key = f"{metrics.service_id}:{metrics.level.value}"
            last_alert = self._last_alerts.get(alert_key)
            
            if not last_alert or (
                datetime.utcnow() - last_alert
            ).total_seconds() > self.config.alert_cooldown:
                await self._trigger_alert(metrics)
                self._last_alerts[alert_key] = datetime.utcnow()

    async def _trigger_alert(self, metrics: HealthMetrics):
        """Trigger health alert"""
        if self.metrics:
            await self.metrics.increment(
                "health.alerts",
                tags={
                    "service": metrics.service_id,
                    "level": metrics.level.value
                }
            )

    async def get_service_metrics(
        self,
        service_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[HealthMetrics]:
        """Get metrics history for a service"""
        metrics = self._metrics_history.get(service_id, [])
        
        if start_time:
            metrics = [m for m in metrics if m.last_check >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.last_check <= end_time]
            
        return metrics

    async def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        stats = {
            "services": len(self._metrics_history),
            "total_metrics": sum(len(m) for m in self._metrics_history.values()),
            "alerts": len(self._last_alerts),
            "service_status": {}
        }
        
        for service_id, metrics in self._metrics_history.items():
            if not metrics:
                continue
                
            latest = metrics[-1]
            stats["service_status"][service_id] = {
                "status": latest.status.value,
                "level": latest.level.value,
                "error_rate": latest.error_rate,
                "response_time": latest.response_time,
                "last_check": latest.last_check.isoformat()
            }
            
        return stats