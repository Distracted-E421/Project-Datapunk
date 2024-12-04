import logging
from dataclasses import dataclass
from typing import Dict, Optional
import psutil
import time
import threading
from concurrent.futures import ThreadPoolExecutor

@dataclass
class ResourceThresholds:
    cpu_threshold: float = 0.8  # 80% CPU utilization threshold
    memory_threshold: float = 0.85  # 85% memory utilization threshold
    io_concurrency: int = 200
    min_free_memory: int = 4 * 1024 * 1024 * 1024  # 4GB in bytes

@dataclass
class ResourceMetrics:
    cpu_usage: float
    memory_usage: float
    io_wait: float
    timestamp: float

class ResourceManager:
    def __init__(
        self,
        thresholds: Optional[ResourceThresholds] = None,
        monitoring_interval: int = 1
    ):
        self.thresholds = thresholds or ResourceThresholds()
        self.monitoring_interval = monitoring_interval
        self.metrics_history: Dict[float, ResourceMetrics] = {}
        self.running = False
        self._lock = threading.Lock()
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.logger = logging.getLogger(__name__)

    def start_monitoring(self):
        """Start the resource monitoring thread."""
        self.running = True
        self.thread_pool.submit(self._monitor_resources)

    def stop_monitoring(self):
        """Stop the resource monitoring thread."""
        self.running = False
        self.thread_pool.shutdown(wait=True)

    def _monitor_resources(self):
        """Continuously monitor system resources."""
        while self.running:
            metrics = self._collect_metrics()
            self._store_metrics(metrics)
            self._handle_resource_pressure(metrics)
            time.sleep(self.monitoring_interval)

    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current system resource metrics."""
        return ResourceMetrics(
            cpu_usage=psutil.cpu_percent(interval=None) / 100.0,
            memory_usage=psutil.virtual_memory().percent / 100.0,
            io_wait=psutil.disk_io_counters().read_time + psutil.disk_io_counters().write_time,
            timestamp=time.time()
        )

    def _store_metrics(self, metrics: ResourceMetrics):
        """Store metrics with timestamp for trend analysis."""
        with self._lock:
            self.metrics_history[metrics.timestamp] = metrics
            # Keep only last hour of metrics
            cutoff_time = time.time() - 3600
            self.metrics_history = {
                k: v for k, v in self.metrics_history.items() 
                if k > cutoff_time
            }

    def _handle_resource_pressure(self, metrics: ResourceMetrics):
        """Handle resource pressure and implement spike handling."""
        if metrics.cpu_usage > self.thresholds.cpu_threshold:
            self._handle_cpu_pressure()
        
        if metrics.memory_usage > self.thresholds.memory_threshold:
            self._handle_memory_pressure()

        if self._detect_spike(metrics):
            self._handle_spike()

    def _handle_cpu_pressure(self):
        """Handle high CPU utilization."""
        self.logger.warning("High CPU utilization detected")
        # Implement CPU pressure handling:
        # 1. Throttle non-critical operations
        # 2. Scale out if possible
        # 3. Defer background tasks

    def _handle_memory_pressure(self):
        """Handle high memory utilization."""
        self.logger.warning("High memory utilization detected")
        # Implement memory pressure handling:
        # 1. Trigger garbage collection
        # 2. Clear caches if necessary
        # 3. Scale out if possible

    def _detect_spike(self, current_metrics: ResourceMetrics) -> bool:
        """Detect resource usage spikes using recent history."""
        if len(self.metrics_history) < 10:  # Need some history for spike detection
            return False

        with self._lock:
            recent_cpu = [m.cpu_usage for m in self.metrics_history.values()]
            avg_cpu = sum(recent_cpu) / len(recent_cpu)
            return current_metrics.cpu_usage > (avg_cpu * 1.5)  # 50% above average

    def _handle_spike(self):
        """Handle detected resource usage spikes."""
        self.logger.warning("Resource usage spike detected")
        # Implement spike handling:
        # 1. Temporarily increase resource limits
        # 2. Enable emergency resource pool
        # 3. Trigger alert if persistent

    def get_resource_allocation(self) -> Dict[str, float]:
        """Get current resource allocation recommendations."""
        metrics = self._collect_metrics()
        return {
            'cpu_allocation': min(1.0, (1 - metrics.cpu_usage) * 0.8),
            'memory_allocation': min(1.0, (1 - metrics.memory_usage) * 0.8),
            'io_concurrency': self.thresholds.io_concurrency
        }

    def adjust_thresholds(self, new_thresholds: ResourceThresholds):
        """Dynamically adjust resource thresholds."""
        self.thresholds = new_thresholds
        self.logger.info("Resource thresholds updated")

    def get_metrics_summary(self) -> Dict[str, float]:
        """Get a summary of recent resource metrics."""
        with self._lock:
            if not self.metrics_history:
                return {}
            
            recent_metrics = list(self.metrics_history.values())
            return {
                'avg_cpu_usage': sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics),
                'avg_memory_usage': sum(m.memory_usage for m in recent_metrics) / len(recent_metrics),
                'peak_cpu_usage': max(m.cpu_usage for m in recent_metrics),
                'peak_memory_usage': max(m.memory_usage for m in recent_metrics)
            } 