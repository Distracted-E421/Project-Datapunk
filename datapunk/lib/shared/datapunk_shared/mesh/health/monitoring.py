from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from .checks import HealthCheck, HealthStatus
from ..discovery.registry import ServiceRegistration
import json
import logging

class MonitoringLevel(Enum):
    """Monitoring severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class HealthMetrics:
    """Health metrics for a service"""
    uptime: float
    error_rate: float
    response_time: float
    memory_usage: float
    cpu_usage: float
    active_connections: int
    last_check: datetime
    status: HealthStatus

@dataclass
class MonitoringConfig:
    """Configuration for health monitoring"""
    check_interval: int = 30  # seconds
    metrics_retention: int = 24 * 60 * 60  # 24 hours in seconds
    alert_threshold: float = 0.8  # 80% threshold for alerts
    log_level: MonitoringLevel = MonitoringLevel.INFO
    enable_persistence: bool = True
    persistence_path: str = "./health_metrics"

class HealthMonitor:
    """Monitors service health and collects metrics"""
    def __init__(
        self,
        config: MonitoringConfig,
        health_check: HealthCheck
    ):
        self.config = config
        self.health_check = health_check
        self._metrics_history: Dict[str, List[HealthMetrics]] = {}
        self._alert_handlers: List[Callable] = []
        self._monitor_task: Optional[asyncio.Task] = None
        self._start_time = datetime.utcnow()
        self.logger = logging.getLogger("health_monitor")
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging for the monitor"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(
            getattr(logging, self.config.log_level.name)
        )

    async def start(self):
        """Start health monitoring"""
        if self.config.enable_persistence:
            await self._load_metrics()
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Health monitoring started")

    async def stop(self):
        """Stop health monitoring"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        if self.config.enable_persistence:
            await self._save_metrics()
        self.logger.info("Health monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                metrics = await self._collect_metrics()
                self._update_metrics_history(metrics)
                await self._check_alerts(metrics)
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {str(e)}")
                await asyncio.sleep(self.config.check_interval)

    async def _collect_metrics(self) -> HealthMetrics:
        """Collect current health metrics"""
        start_time = datetime.utcnow()
        is_healthy = await self.health_check.check_health()
        response_time = (datetime.utcnow() - start_time).total_seconds()

        # Get system metrics (implement these based on your needs)
        memory_usage = await self._get_memory_usage()
        cpu_usage = await self._get_cpu_usage()
        active_connections = await self._get_active_connections()

        return HealthMetrics(
            uptime=(datetime.utcnow() - self._start_time).total_seconds(),
            error_rate=self._calculate_error_rate(),
            response_time=response_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            active_connections=active_connections,
            last_check=datetime.utcnow(),
            status=HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
        )

    def _update_metrics_history(self, metrics: HealthMetrics):
        """Update metrics history with new data"""
        service_id = self.health_check.service_id
        if service_id not in self._metrics_history:
            self._metrics_history[service_id] = []

        self._metrics_history[service_id].append(metrics)

        # Cleanup old metrics
        cutoff_time = datetime.utcnow() - timedelta(
            seconds=self.config.metrics_retention
        )
        self._metrics_history[service_id] = [
            m for m in self._metrics_history[service_id]
            if m.last_check > cutoff_time
        ]

    async def _check_alerts(self, metrics: HealthMetrics):
        """Check metrics against alert thresholds"""
        if metrics.cpu_usage > self.config.alert_threshold:
            await self._trigger_alert(
                "High CPU Usage",
                f"CPU usage at {metrics.cpu_usage*100}%",
                MonitoringLevel.WARNING
            )

        if metrics.memory_usage > self.config.alert_threshold:
            await self._trigger_alert(
                "High Memory Usage",
                f"Memory usage at {metrics.memory_usage*100}%",
                MonitoringLevel.WARNING
            )

        if metrics.status == HealthStatus.UNHEALTHY:
            await self._trigger_alert(
                "Service Unhealthy",
                "Health check failed",
                MonitoringLevel.CRITICAL
            )

    async def _trigger_alert(
        self,
        title: str,
        message: str,
        level: MonitoringLevel
    ):
        """Trigger alerts through registered handlers"""
        alert = {
            "title": title,
            "message": message,
            "level": level.value,
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.health_check.service_id
        }

        for handler in self._alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler error: {str(e)}")

    def add_alert_handler(self, handler: Callable):
        """Add an alert handler"""
        self._alert_handlers.append(handler)

    async def get_health_report(self) -> Dict[str, Any]:
        """Generate health report"""
        service_id = self.health_check.service_id
        metrics = self._metrics_history.get(service_id, [])
        
        if not metrics:
            return {
                "service_id": service_id,
                "status": "UNKNOWN",
                "metrics": None
            }

        latest = metrics[-1]
        return {
            "service_id": service_id,
            "status": latest.status.value,
            "uptime": latest.uptime,
            "metrics": {
                "error_rate": latest.error_rate,
                "response_time": latest.response_time,
                "memory_usage": latest.memory_usage,
                "cpu_usage": latest.cpu_usage,
                "active_connections": latest.active_connections
            },
            "last_check": latest.last_check.isoformat(),
            "historical_data": {
                "error_rates": [m.error_rate for m in metrics[-60:]],  # Last hour
                "response_times": [m.response_time for m in metrics[-60:]]
            }
        }

    async def _save_metrics(self):
        """Save metrics to persistent storage"""
        if not self.config.enable_persistence:
            return

        try:
            metrics_data = {
                service_id: [
                    {
                        **vars(m),
                        "last_check": m.last_check.isoformat(),
                        "status": m.status.value
                    }
                    for m in metrics
                ]
                for service_id, metrics in self._metrics_history.items()
            }

            async with aiofiles.open(
                f"{self.config.persistence_path}/metrics.json", "w"
            ) as f:
                await f.write(json.dumps(metrics_data))
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {str(e)}")

    async def _load_metrics(self):
        """Load metrics from persistent storage"""
        try:
            async with aiofiles.open(
                f"{self.config.persistence_path}/metrics.json", "r"
            ) as f:
                data = json.loads(await f.read())
                
            for service_id, metrics in data.items():
                self._metrics_history[service_id] = [
                    HealthMetrics(
                        **{
                            **m,
                            "last_check": datetime.fromisoformat(m["last_check"]),
                            "status": HealthStatus(m["status"])
                        }
                    )
                    for m in metrics
                ]
        except FileNotFoundError:
            self.logger.info("No saved metrics found")
        except Exception as e:
            self.logger.error(f"Failed to load metrics: {str(e)}")

    # Placeholder methods for system metrics
    async def _get_memory_usage(self) -> float:
        """Get current memory usage"""
        # Implement based on your system
        return 0.0

    async def _get_cpu_usage(self) -> float:
        """Get current CPU usage"""
        # Implement based on your system
        return 0.0

    async def _get_active_connections(self) -> int:
        """Get current active connections"""
        # Implement based on your system
        return 0

    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        # Implement based on your error tracking
        return 0.0 