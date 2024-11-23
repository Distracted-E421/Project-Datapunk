from typing import Dict, Any, List, Callable, Optional
import asyncio
import time
from datetime import datetime
import statistics
from dataclasses import dataclass
import aiohttp
from ..metrics import MetricsCollector
from .monitor import LoadTestMonitor
from pathlib import Path

@dataclass
class LoadTestResult:
    """Container for load test results"""
    name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration: float
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    errors: List[str]
    timestamp: datetime

class LoadTest:
    """Base class for load tests"""
    
    def __init__(
        self,
        name: str,
        metrics: MetricsCollector,
        concurrent_users: int = 10,
        duration: int = 60,
        ramp_up: int = 5,
        monitor: Optional[LoadTestMonitor] = None
    ):
        self.name = name
        self.metrics = metrics
        self.concurrent_users = concurrent_users
        self.duration = duration
        self.ramp_up = ramp_up
        self.results: List[Dict[str, float]] = []
        self.errors: List[str] = []
        self.monitor = monitor or LoadTestMonitor()
        
    async def execute(self) -> LoadTestResult:
        """Execute load test"""
        # Start monitoring
        monitor_task = asyncio.create_task(
            self.monitor.start_monitoring(self.name)
        )
        
        try:
            # Execute test
            result = await super().execute()
            
            # Stop monitoring
            self.monitor.stop_monitoring()
            await monitor_task
            
            # Save monitoring metrics
            if hasattr(self, 'results_dir'):
                self.monitor.save_metrics(Path(self.results_dir))
            
            return result
            
        except Exception as e:
            self.monitor.stop_monitoring()
            await monitor_task
            raise e
    
    async def _user_session(self, user_id: int, start_time: float):
        """Simulate user session"""
        await asyncio.sleep(max(0, start_time - time.time()))
        
        session_start = time.time()
        while time.time() - session_start < self.duration:
            try:
                start = time.time()
                success = await self.user_action(user_id)
                end = time.time()
                
                result = {
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "response_time": end - start,
                    "success": success
                }
                
                self.results.append(result)
                self.monitor.update_request(result)
                
            except Exception as e:
                error = f"User {user_id}: {str(e)}"
                self.errors.append(error)
                self.monitor.update_error(error)
                await asyncio.sleep(1)  # Back off on error
    
    async def user_action(self, user_id: int) -> bool:
        """Override this method to implement specific user actions"""
        raise NotImplementedError 