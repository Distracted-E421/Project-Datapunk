from typing import Dict, Any, List, Optional, Union, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from enum import Enum
import asyncio
import psutil
import numpy as np
from collections import defaultdict, deque
import threading
import queue
import traceback

from .distributed import DistributedManager, Node, NodeState
from .sharding import ShardManager, ShardState
from .consensus import RaftConsensus, NodeRole
from .monitor import IndexMonitor

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics to collect."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class HealthStatus:
    """Node health status."""
    node_id: str
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    open_files: int
    thread_count: int
    error_count: int
    status: str

@dataclass
class PerformanceMetrics:
    """Performance metrics."""
    operation_latency_ms: float
    throughput_ops: float
    error_rate: float
    queue_depth: int
    replication_lag: int
    consensus_rounds: int
    shard_balance_score: float

@dataclass
class Alert:
    """System alert."""
    alert_id: str
    level: AlertLevel
    source: str
    message: str
    timestamp: datetime
    metrics: Dict[str, float]
    context: Dict[str, Any]

class DiagnosticsManager:
    """Manages system diagnostics and monitoring."""
    
    def __init__(
        self,
        distributed: DistributedManager,
        sharding: ShardManager,
        consensus: RaftConsensus,
        monitor: IndexMonitor,
        config_path: Optional[Union[str, Path]] = None
    ):
        self.distributed = distributed
        self.sharding = sharding
        self.consensus = consensus
        self.monitor = monitor
        self.config_path = Path(config_path) if config_path else None
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize state
        self.metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.config["metrics"]["history_size"])
        )
        self.alerts: List[Alert] = []
        self.health_checks: Dict[str, HealthStatus] = {}
        
        # Initialize performance tracking
        self.operation_timings: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        
        # Start monitoring tasks
        self._start_monitoring_tasks()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load diagnostics configuration."""
        if not self.config_path or not self.config_path.exists():
            return {
                "metrics": {
                    "collection_interval_seconds": 10,
                    "history_size": 1000,
                    "aggregation_window_minutes": 5
                },
                "health": {
                    "check_interval_seconds": 30,
                    "cpu_threshold_percent": 80,
                    "memory_threshold_percent": 85,
                    "disk_threshold_percent": 90,
                    "max_error_rate": 0.01
                },
                "alerts": {
                    "max_alerts": 1000,
                    "alert_retention_days": 7,
                    "throttle_interval_seconds": 300
                },
                "tracing": {
                    "enabled": True,
                    "sample_rate": 0.1,
                    "max_spans": 1000
                }
            }
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
            
    def _start_monitoring_tasks(self):
        """Start monitoring background tasks."""
        asyncio.create_task(self._collect_metrics())
        asyncio.create_task(self._check_health())
        asyncio.create_task(self._cleanup_old_data())
        
    async def _collect_metrics(self):
        """Collect system metrics."""
        while True:
            try:
                # Collect distributed metrics
                self._collect_distributed_metrics()
                
                # Collect sharding metrics
                self._collect_sharding_metrics()
                
                # Collect consensus metrics
                self._collect_consensus_metrics()
                
                # Collect system metrics
                self._collect_system_metrics()
                
                await asyncio.sleep(
                    self.config["metrics"]["collection_interval_seconds"]
                )
            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
                
    def _collect_distributed_metrics(self):
        """Collect distributed system metrics."""
        metrics = {
            "active_nodes": len([
                n for n in self.distributed.nodes.values()
                if n.state == NodeState.ACTIVE
            ]),
            "operation_queue_depth": self.distributed._operation_queue.qsize(),
            "replication_lag": self._calculate_replication_lag()
        }
        
        for name, value in metrics.items():
            self.metrics[f"distributed.{name}"].append(
                (datetime.now(), value)
            )
            
    def _collect_sharding_metrics(self):
        """Collect sharding metrics."""
        metrics = {
            "total_shards": len(self.sharding.shards),
            "active_shards": len([
                s for s in self.sharding.shards.values()
                if s.state == ShardState.ACTIVE
            ]),
            "rebalancing_shards": len([
                s for s in self.sharding.shards.values()
                if s.state == ShardState.REBALANCING
            ]),
            "shard_balance_score": self._calculate_shard_balance()
        }
        
        for name, value in metrics.items():
            self.metrics[f"sharding.{name}"].append(
                (datetime.now(), value)
            )
            
    def _collect_consensus_metrics(self):
        """Collect consensus metrics."""
        metrics = {
            "term": self.consensus.state.current_term,
            "log_size": len(self.consensus.state.log),
            "commit_index": self.consensus.state.commit_index,
            "leader_changes": self._count_leader_changes()
        }
        
        for name, value in metrics.items():
            self.metrics[f"consensus.{name}"].append(
                (datetime.now(), value)
            )
            
    def _collect_system_metrics(self):
        """Collect system resource metrics."""
        metrics = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage("/").percent,
            "open_files": len(psutil.Process().open_files()),
            "thread_count": len(psutil.Process().threads())
        }
        
        for name, value in metrics.items():
            self.metrics[f"system.{name}"].append(
                (datetime.now(), value)
            )
            
    async def _check_health(self):
        """Perform health checks."""
        while True:
            try:
                status = self._check_node_health()
                self.health_checks[self.distributed.node_id] = status
                
                # Check thresholds and generate alerts
                self._check_health_thresholds(status)
                
                await asyncio.sleep(
                    self.config["health"]["check_interval_seconds"]
                )
            except Exception as e:
                logger.error(f"Health check error: {str(e)}")
                
    def _check_node_health(self) -> HealthStatus:
        """Check node health status."""
        return HealthStatus(
            node_id=self.distributed.node_id,
            timestamp=datetime.now(),
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage_percent=psutil.disk_usage("/").percent,
            network_io=dict(psutil.net_io_counters()._asdict()),
            open_files=len(psutil.Process().open_files()),
            thread_count=len(psutil.Process().threads()),
            error_count=sum(self.error_counts.values()),
            status=self._determine_health_status()
        )
        
    def _check_health_thresholds(self, status: HealthStatus):
        """Check health metrics against thresholds."""
        thresholds = self.config["health"]
        
        if status.cpu_percent > thresholds["cpu_threshold_percent"]:
            self.create_alert(
                AlertLevel.WARNING,
                "system",
                f"High CPU usage: {status.cpu_percent}%",
                {"cpu_percent": status.cpu_percent}
            )
            
        if status.memory_percent > thresholds["memory_threshold_percent"]:
            self.create_alert(
                AlertLevel.WARNING,
                "system",
                f"High memory usage: {status.memory_percent}%",
                {"memory_percent": status.memory_percent}
            )
            
        if status.disk_usage_percent > thresholds["disk_threshold_percent"]:
            self.create_alert(
                AlertLevel.ERROR,
                "system",
                f"High disk usage: {status.disk_usage_percent}%",
                {"disk_percent": status.disk_usage_percent}
            )
            
    def create_alert(
        self,
        level: AlertLevel,
        source: str,
        message: str,
        metrics: Dict[str, float],
        context: Optional[Dict[str, Any]] = None
    ):
        """Create new alert."""
        alert = Alert(
            alert_id=f"{source}_{datetime.now().timestamp()}",
            level=level,
            source=source,
            message=message,
            timestamp=datetime.now(),
            metrics=metrics,
            context=context or {}
        )
        
        self.alerts.append(alert)
        logger.warning(f"Alert: {message}")
        
        # Trim old alerts
        while len(self.alerts) > self.config["alerts"]["max_alerts"]:
            self.alerts.pop(0)
            
    def _determine_health_status(self) -> str:
        """Determine overall health status."""
        if self._has_critical_issues():
            return "critical"
        elif self._has_warnings():
            return "degraded"
        return "healthy"
        
    def _has_critical_issues(self) -> bool:
        """Check for critical issues."""
        return any(
            a.level == AlertLevel.CRITICAL
            for a in self.alerts[-10:]  # Check recent alerts
        )
        
    def _has_warnings(self) -> bool:
        """Check for warnings."""
        return any(
            a.level in (AlertLevel.WARNING, AlertLevel.ERROR)
            for a in self.alerts[-10:]
        )
        
    def _calculate_replication_lag(self) -> int:
        """Calculate replication lag."""
        if not self.consensus.state.log:
            return 0
            
        leader_index = len(self.consensus.state.log) - 1
        min_follower_index = min(
            self.consensus.match_index.values(),
            default=leader_index
        )
        
        return leader_index - min_follower_index
        
    def _calculate_shard_balance(self) -> float:
        """Calculate shard balance score."""
        node_loads = defaultdict(int)
        for shard in self.sharding.shards.values():
            node_loads[shard.node_id] += shard.size_bytes
            
        if not node_loads:
            return 1.0
            
        loads = list(node_loads.values())
        avg_load = np.mean(loads)
        std_dev = np.std(loads)
        
        if avg_load == 0:
            return 1.0
            
        # Return coefficient of variation (lower is better)
        return 1.0 - min(1.0, std_dev / avg_load)
        
    def _count_leader_changes(self) -> int:
        """Count number of leader changes."""
        leader_metrics = [
            m for m in self.metrics.get("consensus.leader_id", [])
            if m[0] > datetime.now() - timedelta(minutes=5)
        ]
        
        if not leader_metrics:
            return 0
            
        changes = sum(
            1 for i in range(1, len(leader_metrics))
            if leader_metrics[i][1] != leader_metrics[i-1][1]
        )
        
        return changes
        
    async def _cleanup_old_data(self):
        """Clean up old monitoring data."""
        while True:
            try:
                # Clean up old alerts
                cutoff = datetime.now() - timedelta(
                    days=self.config["alerts"]["alert_retention_days"]
                )
                self.alerts = [
                    a for a in self.alerts
                    if a.timestamp > cutoff
                ]
                
                # Clean up old metrics
                for metric_name, values in self.metrics.items():
                    while values and values[0][0] < cutoff:
                        values.popleft()
                        
                await asyncio.sleep(3600)  # Run hourly
                
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")
                
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        return PerformanceMetrics(
            operation_latency_ms=np.mean([
                t for times in self.operation_timings.values()
                for t in times[-100:]  # Last 100 operations
            ]) if self.operation_timings else 0,
            throughput_ops=self._calculate_throughput(),
            error_rate=self._calculate_error_rate(),
            queue_depth=self.distributed._operation_queue.qsize(),
            replication_lag=self._calculate_replication_lag(),
            consensus_rounds=self.consensus.state.current_term,
            shard_balance_score=self._calculate_shard_balance()
        )
        
    def _calculate_throughput(self) -> float:
        """Calculate current throughput."""
        window = timedelta(
            minutes=self.config["metrics"]["aggregation_window_minutes"]
        )
        cutoff = datetime.now() - window
        
        recent_ops = sum(
            1 for times in self.operation_timings.values()
            for t in times
            if t > cutoff.timestamp()
        )
        
        return recent_ops / window.total_seconds()
        
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate."""
        total_ops = sum(
            len(times) for times in self.operation_timings.values()
        )
        total_errors = sum(self.error_counts.values())
        
        if total_ops == 0:
            return 0.0
            
        return total_errors / total_ops