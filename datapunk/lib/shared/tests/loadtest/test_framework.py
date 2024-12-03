import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime
from datapunk_shared.loadtest.framework import (
    LoadTest,
    LoadTestResult,
    MetricsCollector
)

@pytest.fixture
def metrics_collector():
    return Mock(spec=MetricsCollector)

@pytest.fixture
def sample_test():
    class TestLoadTest(LoadTest):
        async def execute_request(self):
            await asyncio.sleep(0.1)
            return True
    
    return TestLoadTest("test_scenario")

@pytest.mark.asyncio
async def test_load_test_initialization(sample_test):
    assert sample_test.name == "test_scenario"
    assert sample_test.active_users == 0
    assert len(sample_test.response_times) == 0

@pytest.mark.asyncio
async def test_load_test_execution():
    test = LoadTest("test")
    with pytest.raises(NotImplementedError):
        await test.execute_request()

@pytest.mark.asyncio
async def test_concurrent_user_simulation(sample_test):
    num_users = 5
    duration = 2
    
    result = await sample_test.run(
        concurrent_users=num_users,
        duration_seconds=duration
    )
    
    assert isinstance(result, LoadTestResult)
    assert result.total_requests > 0
    assert result.successful_requests > 0
    assert result.duration >= duration

@pytest.mark.asyncio
async def test_metrics_collection(sample_test, metrics_collector):
    sample_test.metrics_collector = metrics_collector
    
    await sample_test.run(concurrent_users=2, duration_seconds=1)
    
    metrics_collector.record_response_time.assert_called()
    metrics_collector.record_request_count.assert_called()
    metrics_collector.record_error_count.assert_called()

@pytest.mark.asyncio
async def test_load_test_result_calculation():
    result = LoadTestResult(
        name="test",
        total_requests=100,
        successful_requests=95,
        failed_requests=5,
        duration=10.0,
        avg_response_time=0.1,
        p95_response_time=0.2,
        p99_response_time=0.3
    )
    
    assert result.success_rate == 0.95
    assert result.requests_per_second == 10.0

@pytest.mark.asyncio
async def test_error_handling(sample_test):
    class FailingTest(LoadTest):
        async def execute_request(self):
            raise Exception("Test error")
    
    test = FailingTest("failing_test")
    result = await test.run(concurrent_users=1, duration_seconds=1)
    
    assert result.failed_requests > 0
    assert result.successful_requests == 0

@pytest.mark.asyncio
async def test_user_rampup(sample_test):
    result = await sample_test.run(
        concurrent_users=5,
        duration_seconds=2,
        ramp_up_seconds=1
    )
    
    assert result.total_requests > 0
    # Ramp-up should result in fewer requests than instant start
    assert result.requests_per_second < (result.total_requests / 1.0)

@pytest.mark.asyncio
async def test_response_time_percentiles(sample_test):
    # Mock response times for consistent testing
    sample_test.response_times = [0.1] * 90 + [0.2] * 5 + [0.3] * 5
    
    result = await sample_test.calculate_results(duration=1.0)
    
    assert result.avg_response_time == pytest.approx(0.115)
    assert result.p95_response_time == 0.3
    assert result.p99_response_time == 0.3

@pytest.mark.asyncio
async def test_load_test_cleanup(sample_test):
    await sample_test.run(concurrent_users=2, duration_seconds=1)
    await sample_test.cleanup()
    
    assert sample_test.active_users == 0
    assert not sample_test.is_running

@pytest.mark.asyncio
async def test_concurrent_request_limiting(sample_test):
    max_concurrent = 3
    sample_test.max_concurrent_requests = max_concurrent
    
    # Try to run more concurrent users than allowed
    result = await sample_test.run(
        concurrent_users=max_concurrent + 2,
        duration_seconds=1
    )
    
    # Should be limited to max_concurrent
    assert sample_test.peak_concurrent_requests <= max_concurrent 