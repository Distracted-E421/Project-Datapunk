from typing import Dict, Any, List, Optional, Union, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from enum import Enum
import numpy as np
from collections import defaultdict

from .stats import StatisticsStore
from .manager import IndexManager
from .optimizer import IndexOptimizer

logger = logging.getLogger(__name__)

class IndexHealth(Enum):
    """Index health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    MAINTENANCE = "needs_maintenance"
    REBUILD = "needs_rebuild"

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class PerformanceMetrics:
    """Index performance metrics."""
    query_latency_ms: float
    throughput_qps: float
    cache_hit_ratio: float
    fragmentation_ratio: float
    size_bytes: int
    record_count: int
    last_updated: datetime

@dataclass
class MaintenanceTask:
    """Index maintenance task."""
    index_name: str
    task_type: str
    priority: int
    estimated_duration: timedelta
    impact_level: str
    scheduled_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None

@dataclass
class IndexAlert:
    """Index monitoring alert."""
    index_name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    metrics: Dict[str, float]
    suggested_action: Optional[str] = None

class IndexMonitor:
    """Monitors index health and performance."""
    
    def __init__(
        self,
        store: StatisticsStore,
        manager: IndexManager,
        optimizer: IndexOptimizer,
        config_path: Optional[Union[str, Path]] = None
    ):
        self.store = store
        self.manager = manager
        self.optimizer = optimizer
        self.config_path = Path(config_path) if config_path else None
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize state
        self.metrics: Dict[str, List[PerformanceMetrics]] = defaultdict(list)
        self.health_status: Dict[str, IndexHealth] = {}
        self.maintenance_tasks: List[MaintenanceTask] = []
        self.alerts: List[IndexAlert] = []
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path or not self.config_path.exists():
            return {
                "metrics_retention_days": 30,
                "sampling_interval_seconds": 300,
                "alert_thresholds": {
                    "latency_ms": 100,
                    "throughput_qps": 1000,
                    "cache_hit_ratio": 0.8,
                    "fragmentation_ratio": 0.3,
                    "size_growth_ratio": 1.5
                },
                "health_thresholds": {
                    "degraded": {
                        "latency_factor": 1.5,
                        "cache_hits": 0.7,
                        "fragmentation": 0.2
                    },
                    "critical": {
                        "latency_factor": 3.0,
                        "cache_hits": 0.5,
                        "fragmentation": 0.4
                    }
                }
            }
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
            
    def collect_metrics(self, index_name: str):
        """Collect current performance metrics."""
        stats = self.store.get_latest_stats(index_name)
        if not stats:
            return
            
        metrics = PerformanceMetrics(
            query_latency_ms=stats.usage.avg_read_time_ms,
            throughput_qps=stats.usage.total_reads / 
                max(1, (datetime.now() - stats.created_at).total_seconds()),
            cache_hit_ratio=stats.usage.cache_hits / 
                max(1, stats.usage.cache_hits + stats.usage.cache_misses),
            fragmentation_ratio=stats.size.fragmentation_ratio,
            size_bytes=stats.size.size_bytes,
            record_count=stats.size.total_entries,
            last_updated=datetime.now()
        )
        
        self.metrics[index_name].append(metrics)
        self._cleanup_old_metrics(index_name)
        self._update_health(index_name)
        self._check_alerts(index_name)
        
    def _cleanup_old_metrics(self, index_name: str):
        """Remove metrics older than retention period."""
        retention = timedelta(days=self.config["metrics_retention_days"])
        cutoff = datetime.now() - retention
        
        self.metrics[index_name] = [
            m for m in self.metrics[index_name]
            if m.last_updated > cutoff
        ]
        
    def _update_health(self, index_name: str):
        """Update index health status."""
        if not self.metrics[index_name]:
            return
            
        current = self.metrics[index_name][-1]
        thresholds = self.config["health_thresholds"]
        
        # Calculate baseline from historical metrics
        if len(self.metrics[index_name]) > 1:
            baseline_latency = np.mean([
                m.query_latency_ms
                for m in self.metrics[index_name][:-1]
            ])
            
            # Check for degraded performance
            if (
                current.query_latency_ms > baseline_latency * thresholds["degraded"]["latency_factor"] or
                current.cache_hit_ratio < thresholds["degraded"]["cache_hits"] or
                current.fragmentation_ratio > thresholds["degraded"]["fragmentation"]
            ):
                if (
                    current.query_latency_ms > baseline_latency * thresholds["critical"]["latency_factor"] or
                    current.cache_hit_ratio < thresholds["critical"]["cache_hits"] or
                    current.fragmentation_ratio > thresholds["critical"]["fragmentation"]
                ):
                    self.health_status[index_name] = IndexHealth.CRITICAL
                else:
                    self.health_status[index_name] = IndexHealth.DEGRADED
                    
                # Check if maintenance needed
                if current.fragmentation_ratio > thresholds["degraded"]["fragmentation"]:
                    self._schedule_maintenance(index_name, "REINDEX")
                    self.health_status[index_name] = IndexHealth.MAINTENANCE
            else:
                self.health_status[index_name] = IndexHealth.HEALTHY
                
    def _check_alerts(self, index_name: str):
        """Check for alert conditions."""
        if not self.metrics[index_name]:
            return
            
        current = self.metrics[index_name][-1]
        thresholds = self.config["alert_thresholds"]
        
        # Check various alert conditions
        if current.query_latency_ms > thresholds["latency_ms"]:
            self._create_alert(
                index_name,
                AlertSeverity.WARNING,
                f"High latency: {current.query_latency_ms:.2f}ms",
                {"latency_ms": current.query_latency_ms},
                "Consider index optimization"
            )
            
        if current.cache_hit_ratio < thresholds["cache_hit_ratio"]:
            self._create_alert(
                index_name,
                AlertSeverity.WARNING,
                f"Low cache hit ratio: {current.cache_hit_ratio:.2%}",
                {"cache_hit_ratio": current.cache_hit_ratio},
                "Review index usage patterns"
            )
            
        if current.fragmentation_ratio > thresholds["fragmentation_ratio"]:
            self._create_alert(
                index_name,
                AlertSeverity.ERROR,
                f"High fragmentation: {current.fragmentation_ratio:.2%}",
                {"fragmentation_ratio": current.fragmentation_ratio},
                "Schedule index rebuild"
            )
            
    def _create_alert(
        self,
        index_name: str,
        severity: AlertSeverity,
        message: str,
        metrics: Dict[str, float],
        suggested_action: Optional[str] = None
    ):
        """Create a new alert."""
        alert = IndexAlert(
            index_name=index_name,
            severity=severity,
            message=message,
            timestamp=datetime.now(),
            metrics=metrics,
            suggested_action=suggested_action
        )
        
        self.alerts.append(alert)
        logger.warning(f"Index alert: {message}")
        
    def _schedule_maintenance(
        self,
        index_name: str,
        task_type: str,
        priority: int = 1
    ):
        """Schedule a maintenance task."""
        # Estimate task duration based on index size
        metrics = self.metrics[index_name][-1]
        size_gb = metrics.size_bytes / (1024 * 1024 * 1024)
        estimated_duration = timedelta(minutes=max(5, int(size_gb * 10)))
        
        task = MaintenanceTask(
            index_name=index_name,
            task_type=task_type,
            priority=priority,
            estimated_duration=estimated_duration,
            impact_level="medium" if size_gb < 10 else "high"
        )
        
        # Find next maintenance window
        task.scheduled_time = self._find_maintenance_window(
            estimated_duration
        )
        
        self.maintenance_tasks.append(task)
        
    def _find_maintenance_window(
        self,
        duration: timedelta
    ) -> datetime:
        """Find next available maintenance window."""
        # TODO: Implement maintenance window scheduling
        return datetime.now() + timedelta(hours=1)
        
    def get_health_report(
        self,
        index_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get health report for indexes."""
        if index_name:
            return self._get_single_report(index_name)
            
        return {
            name: self._get_single_report(name)
            for name in self.metrics.keys()
        }
        
    def _get_single_report(self, index_name: str) -> Dict[str, Any]:
        """Get health report for a single index."""
        if not self.metrics[index_name]:
            return {"status": "unknown"}
            
        current = self.metrics[index_name][-1]
        return {
            "status": self.health_status.get(
                index_name,
                IndexHealth.HEALTHY
            ).value,
            "metrics": {
                "latency_ms": current.query_latency_ms,
                "throughput_qps": current.throughput_qps,
                "cache_hit_ratio": current.cache_hit_ratio,
                "fragmentation_ratio": current.fragmentation_ratio,
                "size_bytes": current.size_bytes,
                "record_count": current.record_count
            },
            "maintenance": [
                {
                    "type": task.task_type,
                    "scheduled": task.scheduled_time.isoformat(),
                    "estimated_duration": str(task.estimated_duration),
                    "impact": task.impact_level
                }
                for task in self.maintenance_tasks
                if task.index_name == index_name and
                not task.completed_time
            ],
            "alerts": [
                {
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "suggested_action": alert.suggested_action
                }
                for alert in self.alerts
                if alert.index_name == index_name
            ]
        }