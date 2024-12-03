import unittest
import asyncio
import tempfile
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from aiohttp import ClientSession
from src.infrastructure.load_tester import (
    LoadTester,
    LoadPattern,
    RequestMetrics,
    LoadTestResult
)

class TestLoadTester(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://test-api.example.com"
        self.endpoints = ["/api/v1/test1", "/api/v1/test2"]
        self.tester = LoadTester(
            base_url=self.base_url,
            endpoints=self.endpoints,
            max_users=10,
            test_duration=5,
            ramp_up_time=2
        )

    def test_calculate_users(self):
        """Test user calculation for different load patterns."""
        # Test constant load
        users = self.tester._calculate_users(1, LoadPattern.CONSTANT)
        self.assertEqual(users, self.tester.max_users)

        # Test step load
        users = self.tester._calculate_users(0, LoadPattern.STEP)
        self.assertEqual(users, self.tester.max_users // 4)

        # Test ramp load
        users = self.tester._calculate_users(1, LoadPattern.RAMP)
        self.assertEqual(users, self.tester.max_users // 2)

        # Test spike load
        users = self.tester._calculate_users(0, LoadPattern.SPIKE)
        self.assertEqual(users, self.tester.max_users)

        # Test random load
        users = self.tester._calculate_users(0, LoadPattern.RANDOM)
        self.assertTrue(0 < users <= self.tester.max_users)

    @patch('aiohttp.ClientSession.get')
    async def test_make_request(self, mock_get):
        """Test making individual requests."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = MagicMock(return_value="Success")
        mock_get.return_value.__aenter__.return_value = mock_response

        async with ClientSession() as session:
            await self.tester._make_request(session)

        self.assertEqual(len(self.tester.metrics), 1)
        self.assertTrue(self.tester.metrics[0].success)
        self.assertEqual(self.tester.metrics[0].status_code, 200)

        # Mock failed response
        self.tester.metrics = []
        mock_response.status = 500
        mock_response.text = MagicMock(return_value="Error")

        async with ClientSession() as session:
            await self.tester._make_request(session)

        self.assertEqual(len(self.tester.metrics), 1)
        self.assertFalse(self.tester.metrics[0].success)
        self.assertEqual(self.tester.metrics[0].status_code, 500)

    def test_generate_test_result(self):
        """Test generation of test results."""
        # Add test metrics
        self.tester.metrics = [
            RequestMetrics(
                timestamp=datetime.now(),
                response_time=0.1,
                status_code=200,
                success=True
            ),
            RequestMetrics(
                timestamp=datetime.now(),
                response_time=0.2,
                status_code=200,
                success=True
            ),
            RequestMetrics(
                timestamp=datetime.now(),
                response_time=0.3,
                status_code=500,
                success=False,
                error_message="Internal Server Error"
            )
        ]

        start_time = datetime.now()
        result = self.tester._generate_test_result(start_time, datetime.now())

        self.assertEqual(result.total_requests, 3)
        self.assertEqual(result.successful_requests, 2)
        self.assertEqual(result.failed_requests, 1)
        self.assertEqual(result.min_response_time, 0.1)
        self.assertEqual(result.max_response_time, 0.3)
        self.assertIn("Internal Server Error", result.error_distribution)

    def test_export_results(self):
        """Test exporting results to file."""
        # Create test results
        result = LoadTestResult(
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            avg_response_time=0.2,
            median_response_time=0.18,
            p95_response_time=0.3,
            p99_response_time=0.4,
            min_response_time=0.1,
            max_response_time=0.5,
            requests_per_second=50.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_distribution={"Error": 5}
        )

        # Export to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
            self.tester.export_results(tmp.name, result)
            
            # Read and verify exported data
            with open(tmp.name, 'r') as f:
                exported_data = json.load(f)
                
            self.assertIn('summary', exported_data)
            self.assertIn('detailed_metrics', exported_data)
            self.assertEqual(exported_data['summary']['total_requests'], 100)
            self.assertEqual(exported_data['summary']['successful_requests'], 95)
            
            # Cleanup
            os.unlink(tmp.name)

    def test_analyze_bottlenecks(self):
        """Test bottleneck analysis."""
        # Create test results with issues
        result = LoadTestResult(
            total_requests=100,
            successful_requests=90,
            failed_requests=10,
            avg_response_time=1.5,
            median_response_time=1.2,
            p95_response_time=2.0,
            p99_response_time=2.5,
            min_response_time=0.5,
            max_response_time=3.0,
            requests_per_second=5.0,
            start_time=datetime.now(),
            end_time=datetime.now(),
            error_distribution={"Error": 10}
        )

        analysis = self.tester.analyze_bottlenecks(result)

        self.assertTrue(analysis['response_time_issues'])
        self.assertTrue(analysis['error_rate_issues'])
        self.assertTrue(analysis['throughput_issues'])
        self.assertTrue(len(analysis['recommendations']) > 0)

    @patch('aiohttp.ClientSession.get')
    async def test_distributed_load_test(self, mock_get):
        """Test distributed load testing."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = MagicMock(return_value="Success")
        mock_get.return_value.__aenter__.return_value = mock_response

        worker_urls = ["http://worker1", "http://worker2"]
        result = await self.tester.run_distributed_load_test(worker_urls)

        self.assertIsInstance(result, LoadTestResult)
        self.assertTrue(result.total_requests > 0)

    @patch('aiohttp.ClientSession.get')
    async def test_custom_scenario(self, mock_get):
        """Test custom test scenario execution."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = MagicMock(return_value="Success")
        mock_get.return_value.__aenter__.return_value = mock_response

        # Create test scenario
        scenario = TestScenario(
            name="Test Scenario",
            steps=[
                {
                    'duration': 2,
                    'users': 5,
                    'pattern': LoadPattern.CONSTANT,
                    'think_time': 0.1
                },
                {
                    'duration': 2,
                    'users': 10,
                    'pattern': LoadPattern.RAMP
                }
            ],
            think_time=0.1,
            success_criteria={
                'max_response_time': 1.0,
                'min_rps': 1.0,
                'max_error_rate': 0.1
            }
        )

        result = await self.tester.run_custom_scenario(scenario)
        
        self.assertIsInstance(result, LoadTestResult)
        self.assertTrue(result.total_requests > 0)
        self.assertTrue(result.successful_requests > 0)

    @patch('aiohttp.ClientSession.get')
    async def test_real_time_monitoring(self, mock_get):
        """Test real-time monitoring capabilities."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = MagicMock(return_value="Success")
        mock_get.return_value.__aenter__.return_value = mock_response

        # Create monitoring callback
        metrics_received = []
        def monitoring_callback(metrics):
            metrics_received.append(metrics)

        # Start monitoring
        await self.tester.start_monitoring(monitoring_callback)

        # Run a short test
        await self.tester.run_load_test(pattern=LoadPattern.CONSTANT)

        # Stop monitoring
        await self.tester.stop_monitoring()

        # Verify metrics were collected
        self.assertTrue(len(metrics_received) > 0)
        for metrics in metrics_received:
            self.assertIn('current_users', metrics)
            self.assertIn('active_requests', metrics)
            self.assertIn('success_rate', metrics)
            self.assertIn('avg_response_time', metrics)
            self.assertIn('requests_per_second', metrics)

    @patch('aiohttp.ClientSession.get')
    async def test_success_criteria_validation(self, mock_get):
        """Test validation of success criteria."""
        # Mock slow response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = MagicMock(return_value="Success")
        mock_get.return_value.__aenter__.return_value = mock_response

        # Create scenario with strict criteria
        scenario = TestScenario(
            name="Strict Test",
            steps=[
                {
                    'duration': 2,
                    'users': 5,
                    'pattern': LoadPattern.CONSTANT
                }
            ],
            success_criteria={
                'max_response_time': 0.001,  # Very strict criteria
                'min_rps': 1000,            # Impossible to achieve
                'max_error_rate': 0.0       # No errors allowed
            }
        )

        # Test should fail due to strict criteria
        with self.assertRaises(AssertionError) as context:
            await self.tester.run_custom_scenario(scenario)
        
        error_message = str(context.exception)
        self.assertIn("Test failed success criteria", error_message)

    def test_real_time_metrics(self):
        """Test real-time metrics calculations."""
        metrics = RealTimeMetrics()
        
        # Test initial state
        stats = metrics.get_current_stats()
        self.assertEqual(stats['current_users'], 0)
        self.assertEqual(stats['active_requests'], 0)
        self.assertEqual(stats['success_rate'], 0)
        self.assertEqual(stats['avg_response_time'], 0)
        self.assertEqual(stats['requests_per_second'], 0)

        # Test metrics update
        async def update_metrics():
            await metrics.update(RequestMetrics(
                timestamp=datetime.now(),
                response_time=0.1,
                status_code=200,
                success=True
            ))
            await metrics.update(RequestMetrics(
                timestamp=datetime.now(),
                response_time=0.2,
                status_code=500,
                success=False
            ))

        loop = asyncio.get_event_loop()
        loop.run_until_complete(update_metrics())

        # Test updated stats
        stats = metrics.get_current_stats()
        self.assertEqual(stats['success_rate'], 0.5)  # 1 success, 1 failure
        self.assertEqual(stats['avg_response_time'], 0.15)  # (0.1 + 0.2) / 2

def async_test(coro):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

if __name__ == '__main__':
    unittest.main() 