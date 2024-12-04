"""
Load Test Runner and Results Management System

Orchestrates the execution of load tests across the Datapunk service mesh
and manages result collection, storage, and reporting. Integrates with the
monitoring system for comprehensive performance analysis.

Key responsibilities:
- Sequential test execution with monitoring
- Result aggregation and persistence
- Integration with benchmark reporting system
- Resource cleanup and error handling

See sys-arch.mmd Infrastructure/Testing for integration details.
"""

from typing import List, Dict, Any
import asyncio
from datetime import datetime
import json
from pathlib import Path
from .framework import LoadTest, LoadTestResult
from ..benchmarks.reporter import BenchmarkReporter
from .monitor import LoadTestMonitor

class LoadTestRunner:
    """
    Orchestrates load test execution and result management.
    
    Provides a centralized system for running load tests, collecting results,
    and generating reports. Integrates with the broader Datapunk observability
    stack for comprehensive performance analysis.
    
    TODO: Add parallel test execution support
    TODO: Implement test dependency management
    FIXME: Improve error aggregation across test suite
    """
    
    def __init__(self, results_dir: str = "loadtest_results"):
        """
        Initialize runner with configurable results storage.
        
        NOTE: Results directory is created if it doesn't exist to ensure
        consistent test result storage across runs.
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.reporter = BenchmarkReporter(results_dir)
        self.monitor = LoadTestMonitor()
        
    async def run_tests(self, tests: List[LoadTest]) -> List[LoadTestResult]:
        """
        Execute a suite of load tests sequentially.
        
        Manages test lifecycle, monitoring, and result collection. Tests
        are run sequentially to prevent resource contention and ensure
        accurate measurements.
        
        TODO: Add test warmup/cooldown periods
        TODO: Implement resource usage thresholds
        """
        results = []
        
        for test in tests:
            # Configure test monitoring
            test.monitor = self.monitor
            test.results_dir = self.results_dir
            
            result = await test.execute()
            results.append(result)
            
            # Persist individual test results
            self._save_test_result(result)
            
        # Generate consolidated report
        self._generate_report(results)
        
        return results
    
    def _save_test_result(self, result: LoadTestResult):
        """
        Persist individual test results to JSON.
        
        Results are stored with timestamps to enable historical analysis
        and trend detection. Format is compatible with Datapunk's
        analytics pipeline.
        
        NOTE: All timestamps are stored in ISO format for consistent
        parsing across different tools.
        """
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
        """
        Generate consolidated performance report.
        
        Converts load test results into benchmark format for integration
        with Datapunk's reporting system. This enables consistent
        performance tracking across different types of tests.
        
        NOTE: Error rates are normalized to percentages for easier
        interpretation in reports.
        """
        # Transform results to benchmark format
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