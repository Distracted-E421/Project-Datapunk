from typing import List, Dict, Any
import asyncio
from datetime import datetime
import json
from pathlib import Path
from .framework import LoadTest, LoadTestResult
from ..benchmarks.reporter import BenchmarkReporter
from .monitor import LoadTestMonitor

class LoadTestRunner:
    """Run and report load tests"""
    
    def __init__(self, results_dir: str = "loadtest_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.reporter = BenchmarkReporter(results_dir)
        self.monitor = LoadTestMonitor()
        
    async def run_tests(self, tests: List[LoadTest]) -> List[LoadTestResult]:
        """Run multiple load tests sequentially"""
        results = []
        
        for test in tests:
            # Set up monitoring
            test.monitor = self.monitor
            test.results_dir = self.results_dir
            
            result = await test.execute()
            results.append(result)
            
            # Save individual test results
            self._save_test_result(result)
            
        # Generate report
        self._generate_report(results)
        
        return results
    
    def _save_test_result(self, result: LoadTestResult):
        """Save individual test result"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        result_file = self.results_dir / f"loadtest_{result.name}_{timestamp}.json"
        
        with open(result_file, 'w') as f:
            json.dump({
                "name": result.name,
                "timestamp": result.timestamp.isoformat(),
                "metrics": {
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "duration": result.duration,
                    "avg_response_time": result.avg_response_time,
                    "p95_response_time": result.p95_response_time,
                    "p99_response_time": result.p99_response_time,
                    "requests_per_second": result.requests_per_second
                },
                "errors": result.errors
            }, f, indent=2)
    
    def _generate_report(self, results: List[LoadTestResult]):
        """Generate load test report"""
        # Convert results to benchmark format
        benchmark_results = []
        
        for result in results:
            benchmark_results.append({
                "name": result.name,
                "operation": "Load Test",
                "iterations": result.total_requests,
                "timings": {
                    "mean": result.avg_response_time,
                    "p95": result.p95_response_time,
                    "p99": result.p99_response_time,
                    "min": min(result.avg_response_time, result.p95_response_time),
                    "max": max(result.p95_response_time, result.p99_response_time)
                },
                "resources": {
                    "requests_per_second": result.requests_per_second,
                    "error_rate": (result.failed_requests / result.total_requests) * 100
                }
            })
        
        # Generate report using benchmark reporter
        self.reporter.generate_report(benchmark_results) 