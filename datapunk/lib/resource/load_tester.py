import logging
import asyncio
import aiohttp
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import statistics
import json
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from enum import Enum

class LoadPattern(Enum):
    CONSTANT = "constant"
    STEP = "step"
    RAMP = "ramp"
    SPIKE = "spike"
    RANDOM = "random"

@dataclass
class RequestMetrics:
    timestamp: datetime
    response_time: float
    status_code: int
    success: bool
    error_message: Optional[str] = None

@dataclass
class LoadTestResult:
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    start_time: datetime
    end_time: datetime
    error_distribution: Dict[str, int]

@dataclass
class TestScenario:
    name: str
    steps: List[Dict[str, Any]]
    think_time: Optional[float] = None
    success_criteria: Optional[Dict[str, float]] = None

class RealTimeMetrics:
    def __init__(self):
        self.current_users: int = 0
        self.active_requests: int = 0
        self.success_count: int = 0
        self.error_count: int = 0
        self.recent_response_times: List[float] = []
        self.start_time: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def update(self, metric: RequestMetrics):
        async with self._lock:
            if not self.start_time:
                self.start_time = datetime.now()
            
            if metric.success:
                self.success_count += 1
            else:
                self.error_count += 1
            
            self.recent_response_times.append(metric.response_time)
            if len(self.recent_response_times) > 100:
                self.recent_response_times.pop(0)

    def get_current_stats(self) -> Dict[str, Any]:
        if not self.recent_response_times:
            return {
                'current_users': self.current_users,
                'active_requests': self.active_requests,
                'success_rate': 0,
                'avg_response_time': 0,
                'requests_per_second': 0
            }

        total_requests = self.success_count + self.error_count
        success_rate = self.success_count / total_requests if total_requests > 0 else 0
        avg_response_time = sum(self.recent_response_times) / len(self.recent_response_times)
        
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        rps = total_requests / elapsed_time if elapsed_time > 0 else 0

        return {
            'current_users': self.current_users,
            'active_requests': self.active_requests,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'requests_per_second': rps
        }

class LoadTester:
    def __init__(
        self,
        base_url: str,
        endpoints: List[str],
        max_users: int = 100,
        test_duration: int = 300,
        ramp_up_time: int = 30,
        timeout: float = 30.0,
        custom_headers: Optional[Dict[str, str]] = None,
        monitoring_interval: float = 1.0
    ):
        self.base_url = base_url
        self.endpoints = endpoints
        self.max_users = max_users
        self.test_duration = test_duration
        self.ramp_up_time = ramp_up_time
        self.timeout = timeout
        self.custom_headers = custom_headers or {}
        self.metrics: List[RequestMetrics] = []
        self.logger = logging.getLogger(__name__)
        self._executor = ThreadPoolExecutor(max_workers=max_users)
        self.real_time_metrics = RealTimeMetrics()
        self.monitoring_interval = monitoring_interval
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    async def run_load_test(
        self,
        pattern: LoadPattern = LoadPattern.CONSTANT,
        custom_load_function: Optional[Callable[[int], int]] = None
    ) -> LoadTestResult:
        """Run load test with specified pattern."""
        start_time = datetime.now()
        self.metrics = []
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            tasks = []
            for second in range(self.test_duration):
                current_users = self._calculate_users(second, pattern, custom_load_function)
                tasks.extend([
                    self._make_request(session)
                    for _ in range(current_users)
                ])
                
                if tasks:
                    await asyncio.gather(*tasks)
                    tasks = []
                
                await asyncio.sleep(1)  # Wait for next second

        return self._generate_test_result(start_time, datetime.now())

    def _calculate_users(
        self,
        current_second: int,
        pattern: LoadPattern,
        custom_function: Optional[Callable[[int], int]] = None
    ) -> int:
        """Calculate number of users for current second based on pattern."""
        if custom_function:
            return min(custom_function(current_second), self.max_users)

        if pattern == LoadPattern.CONSTANT:
            return self.max_users

        elif pattern == LoadPattern.STEP:
            step_duration = self.test_duration // 4
            step = current_second // step_duration
            return min(self.max_users * (step + 1) // 4, self.max_users)

        elif pattern == LoadPattern.RAMP:
            if current_second < self.ramp_up_time:
                return int(self.max_users * current_second / self.ramp_up_time)
            return self.max_users

        elif pattern == LoadPattern.SPIKE:
            spike_interval = self.test_duration // 3
            if current_second % spike_interval < spike_interval // 4:
                return self.max_users
            return self.max_users // 2

        elif pattern == LoadPattern.RANDOM:
            return np.random.randint(1, self.max_users + 1)

        return self.max_users

    async def _make_request(self, session: aiohttp.ClientSession) -> None:
        """Make a single request and record metrics."""
        self.real_time_metrics.active_requests += 1
        try:
            endpoint = np.random.choice(self.endpoints)
            url = f"{self.base_url}{endpoint}"
            start_time = time.time()
            
            try:
                async with session.get(url, headers=self.custom_headers) as response:
                    response_time = time.time() - start_time
                    success = 200 <= response.status < 400
                    
                    metric = RequestMetrics(
                        timestamp=datetime.now(),
                        response_time=response_time,
                        status_code=response.status,
                        success=success,
                        error_message=None if success else await response.text()
                    )
                    self.metrics.append(metric)
                    
                    await self.real_time_metrics.update(metric)
            except Exception as e:
                response_time = time.time() - start_time
                metric = RequestMetrics(
                    timestamp=datetime.now(),
                    response_time=response_time,
                    status_code=0,
                    success=False,
                    error_message=str(e)
                )
                self.metrics.append(metric)
        finally:
            self.real_time_metrics.active_requests -= 1

    def _generate_test_result(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> LoadTestResult:
        """Generate test result summary."""
        response_times = [m.response_time for m in self.metrics]
        successful_requests = len([m for m in self.metrics if m.success])
        failed_requests = len(self.metrics) - successful_requests
        
        error_distribution = {}
        for metric in self.metrics:
            if not metric.success and metric.error_message:
                error_distribution[metric.error_message] = (
                    error_distribution.get(metric.error_message, 0) + 1
                )

        test_duration = (end_time - start_time).total_seconds()
        
        return LoadTestResult(
            total_requests=len(self.metrics),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times),
            median_response_time=statistics.median(response_times),
            p95_response_time=np.percentile(response_times, 95),
            p99_response_time=np.percentile(response_times, 99),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            requests_per_second=len(self.metrics) / test_duration,
            start_time=start_time,
            end_time=end_time,
            error_distribution=error_distribution
        )

    def export_results(self, file_path: str, result: LoadTestResult) -> None:
        """Export test results to a JSON file."""
        result_dict = {
            'summary': {
                'total_requests': result.total_requests,
                'successful_requests': result.successful_requests,
                'failed_requests': result.failed_requests,
                'avg_response_time': result.avg_response_time,
                'median_response_time': result.median_response_time,
                'p95_response_time': result.p95_response_time,
                'p99_response_time': result.p99_response_time,
                'min_response_time': result.min_response_time,
                'max_response_time': result.max_response_time,
                'requests_per_second': result.requests_per_second,
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat(),
                'error_distribution': result.error_distribution
            },
            'detailed_metrics': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'response_time': m.response_time,
                    'status_code': m.status_code,
                    'success': m.success,
                    'error_message': m.error_message
                }
                for m in self.metrics
            ]
        }
        
        with open(file_path, 'w') as f:
            json.dump(result_dict, f, indent=2)

    async def run_distributed_load_test(
        self,
        worker_urls: List[str],
        pattern: LoadPattern = LoadPattern.CONSTANT
    ) -> LoadTestResult:
        """Run load test distributed across multiple workers."""
        start_time = datetime.now()
        worker_count = len(worker_urls)
        users_per_worker = self.max_users // worker_count
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for worker_url in worker_urls:
                worker = LoadTester(
                    base_url=self.base_url,
                    endpoints=self.endpoints,
                    max_users=users_per_worker,
                    test_duration=self.test_duration,
                    ramp_up_time=self.ramp_up_time,
                    timeout=self.timeout,
                    custom_headers=self.custom_headers
                )
                tasks.append(worker.run_load_test(pattern))
            
            worker_results = await asyncio.gather(*tasks)
        
        # Combine results
        total_metrics = []
        for result in worker_results:
            total_metrics.extend(self.metrics)
        
        self.metrics = total_metrics
        return self._generate_test_result(start_time, datetime.now())

    def analyze_bottlenecks(self, result: LoadTestResult) -> Dict[str, Any]:
        """Analyze test results for potential bottlenecks."""
        analysis = {
            'response_time_issues': False,
            'error_rate_issues': False,
            'throughput_issues': False,
            'recommendations': []
        }
        
        # Check response time
        if result.p95_response_time > 1.0:  # More than 1 second for 95th percentile
            analysis['response_time_issues'] = True
            analysis['recommendations'].append(
                "High response times detected. Consider optimizing server processing or scaling up."
            )
        
        # Check error rate
        error_rate = result.failed_requests / result.total_requests
        if error_rate > 0.05:  # More than 5% errors
            analysis['error_rate_issues'] = True
            analysis['recommendations'].append(
                f"High error rate ({error_rate:.2%}). Investigate error patterns in error_distribution."
            )
        
        # Check throughput
        if result.requests_per_second < self.max_users / 10:  # Less than 10% of theoretical max
            analysis['throughput_issues'] = True
            analysis['recommendations'].append(
                "Low throughput detected. Consider checking for connection pooling or database bottlenecks."
            )
        
        return analysis 

    async def run_custom_scenario(
        self,
        scenario: TestScenario
    ) -> LoadTestResult:
        """Run a custom test scenario."""
        start_time = datetime.now()
        self.metrics = []
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            for step in scenario.steps:
                # Get step parameters
                duration = step.get('duration', 60)  # seconds
                users = step.get('users', self.max_users)
                pattern = step.get('pattern', LoadPattern.CONSTANT)
                think_time = step.get('think_time', scenario.think_time)
                
                # Execute step
                tasks = []
                for second in range(duration):
                    current_users = self._calculate_users(second, pattern)
                    adjusted_users = min(current_users, users)
                    
                    self.real_time_metrics.current_users = adjusted_users
                    
                    for _ in range(adjusted_users):
                        tasks.append(self._make_request(session))
                        if think_time:
                            await asyncio.sleep(think_time)
                    
                    if tasks:
                        await asyncio.gather(*tasks)
                        tasks = []
                    
                    await asyncio.sleep(1)

        result = self._generate_test_result(start_time, datetime.now())
        
        # Check success criteria if defined
        if scenario.success_criteria:
            self._check_success_criteria(result, scenario.success_criteria)
            
        return result

    def _check_success_criteria(
        self,
        result: LoadTestResult,
        criteria: Dict[str, float]
    ) -> None:
        """Check if test results meet success criteria."""
        failures = []
        
        if 'max_response_time' in criteria:
            if result.p95_response_time > criteria['max_response_time']:
                failures.append(
                    f"P95 response time {result.p95_response_time:.2f}s exceeds maximum {criteria['max_response_time']}s"
                )
        
        if 'min_rps' in criteria:
            if result.requests_per_second < criteria['min_rps']:
                failures.append(
                    f"Requests per second {result.requests_per_second:.2f} below minimum {criteria['min_rps']}"
                )
        
        if 'max_error_rate' in criteria:
            error_rate = result.failed_requests / result.total_requests
            if error_rate > criteria['max_error_rate']:
                failures.append(
                    f"Error rate {error_rate:.2%} exceeds maximum {criteria['max_error_rate']:.2%}"
                )
        
        if failures:
            raise AssertionError("Test failed success criteria:\n" + "\n".join(failures))

    async def start_monitoring(
        self,
        callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Start real-time monitoring with callback for metrics updates."""
        self._monitoring_callback = callback
        self._monitoring_task = asyncio.create_task(self._monitor_metrics())

    async def stop_monitoring(self) -> None:
        """Stop real-time monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            self._monitoring_callback = None

    async def _monitor_metrics(self) -> None:
        """Monitor and report metrics periodically."""
        while True:
            if self._monitoring_callback:
                stats = self.real_time_metrics.get_current_stats()
                self._monitoring_callback(stats)
            await asyncio.sleep(self.monitoring_interval)