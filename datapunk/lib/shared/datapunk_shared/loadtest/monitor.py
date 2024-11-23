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
    """Container for real-time metrics"""
    active_users: int
    requests_per_second: float
    current_error_rate: float
    avg_response_time: float
    p95_response_time: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime

class LoadTestMonitor:
    """Real-time monitoring for load tests"""
    
    def __init__(self, update_interval: float = 1.0):
        self.update_interval = update_interval
        self.metrics_history: List[RealTimeMetrics] = []
        self.current_metrics: Optional[RealTimeMetrics] = None
        self.is_running = False
        self._screen = None
        self._recent_requests: List[Dict[str, Any]] = []
        self._recent_errors: List[str] = []
        
    async def start_monitoring(self, test_name: str):
        """Start monitoring in a separate task"""
        self.is_running = True
        self.test_name = test_name
        self._screen = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        
        try:
            while self.is_running:
                self._update_metrics()
                self._draw_screen()
                await asyncio.sleep(self.update_interval)
        finally:
            curses.endwin()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_running = False
        if self._screen:
            curses.endwin()
    
    def update_request(self, request_data: Dict[str, Any]):
        """Update with new request data"""
        self._recent_requests.append(request_data)
        # Keep last 1000 requests for calculations
        if len(self._recent_requests) > 1000:
            self._recent_requests.pop(0)
    
    def update_error(self, error: str):
        """Update with new error"""
        self._recent_errors.append(error)
        # Keep last 100 errors
        if len(self._recent_errors) > 100:
            self._recent_errors.pop(0)
    
    def _update_metrics(self):
        """Calculate current metrics"""
        now = datetime.utcnow()
        
        # Calculate metrics from recent requests
        recent_times = [r["response_time"] for r in self._recent_requests]
        if recent_times:
            avg_time = statistics.mean(recent_times)
            p95_time = sorted(recent_times)[int(len(recent_times) * 0.95)]
            error_rate = len(self._recent_errors) / len(self._recent_requests)
            rps = len(recent_times) / self.update_interval
        else:
            avg_time = 0
            p95_time = 0
            error_rate = 0
            rps = 0
        
        # System metrics
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
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
        """Draw monitoring screen"""
        if not self._screen or not self.current_metrics:
            return
            
        self._screen.clear()
        
        # Draw title
        self._screen.addstr(0, 0, f"Load Test Monitor - {self.test_name}", curses.A_BOLD)
        self._screen.addstr(1, 0, "=" * 50)
        
        # Draw metrics
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
        
        # Draw recent errors
        y += 2
        self._screen.addstr(y, 0, "Recent Errors:", curses.A_BOLD)
        for i, error in enumerate(reversed(self._recent_errors[-5:])):
            if y + i + 1 < curses.LINES:
                self._screen.addstr(y + i + 1, 2, error[:curses.COLS-4], 
                                  curses.color_pair(2))
        
        self._screen.refresh()
    
    def save_metrics(self, output_dir: Path):
        """Save metrics history to file"""
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