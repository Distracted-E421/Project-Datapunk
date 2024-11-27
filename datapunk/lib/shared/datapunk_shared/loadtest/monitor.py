"""
Real-Time Load Test Monitoring System

Provides real-time visualization and metrics collection for Datapunk load tests.
Integrates with the service mesh monitoring infrastructure to provide comprehensive
insights into system behavior under load.

Key features:
- Real-time metrics visualization using curses
- System resource monitoring (CPU, memory)
- Error tracking and analysis
- Metrics persistence for post-test analysis

See sys-arch.mmd Infrastructure/Observability for integration details.
"""

from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import statistics
from dataclasses import dataclass
import curses
import json
from pathlib import Path
import psutil

@dataclass
class RealTimeMetrics:
    """
    Container for real-time performance metrics.
    
    Aggregates both application-level metrics (requests, errors) and
    system-level metrics (CPU, memory) for comprehensive monitoring.
    
    NOTE: All timestamps are in UTC for consistent analysis across zones.
    """
    active_users: int
    requests_per_second: float
    current_error_rate: float
    avg_response_time: float
    p95_response_time: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime

class LoadTestMonitor:
    """
    Real-time monitoring and visualization for load tests.
    
    Provides a curses-based interface for monitoring test progress and
    system health. Integrates with Prometheus and Grafana for long-term
    metrics storage and analysis.
    
    TODO: Add network I/O monitoring
    TODO: Implement metric export to Prometheus
    FIXME: Improve error categorization for better analysis
    """
    
    def __init__(self, update_interval: float = 1.0):
        """
        Initialize monitor with configurable update interval.
        
        NOTE: Default 1-second interval balances responsiveness with
        system overhead. Adjust based on test requirements and system
        capabilities.
        """
        self.update_interval = update_interval
        self.metrics_history: List[RealTimeMetrics] = []
        self.current_metrics: Optional[RealTimeMetrics] = None
        self.is_running = False
        self._screen = None
        self._recent_requests: List[Dict[str, Any]] = []
        self._recent_errors: List[str] = []
        
    async def start_monitoring(self, test_name: str):
        """
        Initialize and start the monitoring interface.
        
        Sets up curses display and color pairs for the TUI. Colors are used
        to indicate metric status (green=good, yellow=warning, red=critical).
        
        NOTE: Curses initialization must be handled carefully to avoid
        terminal corruption on unexpected exits.
        """
        self.is_running = True
        self.test_name = test_name
        self._screen = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)   # Good status
        curses.init_pair(2, curses.COLOR_RED, -1)     # Critical status
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # Warning status
        
        try:
            while self.is_running:
                self._update_metrics()
                self._draw_screen()
                await asyncio.sleep(self.update_interval)
        finally:
            curses.endwin()  # Ensure terminal is restored
    
    def stop_monitoring(self):
        """
        Safely terminate monitoring and restore terminal state.
        
        NOTE: This method must be called even if monitoring fails to
        ensure proper terminal cleanup.
        """
        self.is_running = False
        if self._screen:
            curses.endwin()
    
    def update_request(self, request_data: Dict[str, Any]):
        """
        Update metrics with new request data.
        
        Maintains a rolling window of recent requests for calculating
        moving averages and percentiles.
        
        NOTE: Window size of 1000 requests chosen to balance memory
        usage with statistical significance.
        """
        self._recent_requests.append(request_data)
        if len(self._recent_requests) > 1000:
            self._recent_requests.pop(0)
    
    def update_error(self, error: str):
        """
        Track new error occurrences.
        
        Maintains recent error history for pattern analysis and
        real-time monitoring.
        
        TODO: Implement error categorization and pattern detection
        """
        self._recent_errors.append(error)
        if len(self._recent_errors) > 100:
            self._recent_errors.pop(0)
    
    def _update_metrics(self):
        """
        Calculate current performance metrics.
        
        Aggregates request metrics and system resource usage into
        a comprehensive snapshot of system performance.
        
        NOTE: System metrics collection may impact performance under
        extreme load conditions.
        """
        now = datetime.utcnow()
        
        # Calculate metrics from recent requests
        recent_times = [r["response_time"] for r in self._recent_requests]
        if recent_times:
            avg_time = statistics.mean(recent_times)
            p95_time = sorted(recent_times)[int(len(recent_times) * 0.95)]
            error_rate = len(self._recent_errors) / len(self._recent_requests)
            rps = len(recent_times) / self.update_interval
        else:
            avg_time = p95_time = error_rate = rps = 0
        
        # System metrics via psutil
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        cpu_usage = process.cpu_percent()
        
        self.current_metrics = RealTimeMetrics(
            active_users=len(set(r["user_id"] for r in self._recent_requests)),
            requests_per_second=rps,
            current_error_rate=error_rate,
            avg_response_time=avg_time,
            p95_response_time=p95_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            timestamp=now
        )
        
        self.metrics_history.append(self.current_metrics)
    
    def _draw_screen(self):
        """
        Update the TUI with current metrics.
        
        Uses color coding to highlight critical metrics:
        - Green: Normal operation
        - Yellow: Warning thresholds
        - Red: Critical thresholds
        
        TODO: Make thresholds configurable
        TODO: Add graphical trends using ASCII charts
        """
        if not self._screen or not self.current_metrics:
            return
            
        self._screen.clear()
        
        # Draw title and header
        self._screen.addstr(0, 0, f"Load Test Monitor - {self.test_name}", curses.A_BOLD)
        self._screen.addstr(1, 0, "=" * 50)
        
        # Draw metrics with color-coded status
        y = 3
        self._screen.addstr(y, 0, "Active Users: ")
        self._screen.addstr(y, 15, str(self.current_metrics.active_users), 
                          curses.color_pair(1))
        
        y += 1
        self._screen.addstr(y, 0, "Requests/sec: ")
        self._screen.addstr(y, 15, f"{self.current_metrics.requests_per_second:.2f}", 
                          curses.color_pair(1))
        
        y += 1
        self._screen.addstr(y, 0, "Error Rate: ")
        color = 1 if self.current_metrics.current_error_rate < 0.05 else 2
        self._screen.addstr(y, 15, f"{self.current_metrics.current_error_rate:.2%}", 
                          curses.color_pair(color))
        
        y += 1
        self._screen.addstr(y, 0, "Avg Response: ")
        self._screen.addstr(y, 15, f"{self.current_metrics.avg_response_time:.3f}s", 
                          curses.color_pair(1))
        
        y += 1
        self._screen.addstr(y, 0, "P95 Response: ")
        self._screen.addstr(y, 15, f"{self.current_metrics.p95_response_time:.3f}s", 
                          curses.color_pair(1))
        
        # Draw recent errors section
        y += 2
        self._screen.addstr(y, 0, "Recent Errors:", curses.A_BOLD)
        for i, error in enumerate(reversed(self._recent_errors[-5:])):
            if y + i + 1 < curses.LINES:
                self._screen.addstr(y + i + 1, 2, error[:curses.COLS-4], 
                                  curses.color_pair(2))
        
        self._screen.refresh()
    
    def save_metrics(self, output_dir: Path):
        """
        Persist metrics history to JSON for post-test analysis.
        
        Integrates with Datapunk's observability stack for long-term
        storage and analysis in Grafana.
        
        TODO: Add metric export to Prometheus/Grafana
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        metrics_file = output_dir / f"metrics_{self.test_name}_{timestamp}.json"
        
        metrics_data = [
            {
                "timestamp": m.timestamp.isoformat(),
                "active_users": m.active_users,
                "requests_per_second": m.requests_per_second,
                "error_rate": m.current_error_rate,
                "avg_response_time": m.avg_response_time,
                "p95_response_time": m.p95_response_time,
                "memory_usage": m.memory_usage,
                "cpu_usage": m.cpu_usage
            }
            for m in self.metrics_history
        ]
        
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2) 