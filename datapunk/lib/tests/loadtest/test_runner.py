import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from pathlib import Path
import json
from datapunk_shared.loadtest.runner import (
    LoadTestRunner,
    LoadTest,
    LoadTestResult,
    BenchmarkReporter
)

@pytest.fixture
def mock_reporter():
    return Mock(spec=BenchmarkReporter)

@pytest.fixture
def test_results_dir(tmp_path):
    return tmp_path / "loadtest_results"

@pytest.fixture
def runner(test_results_dir, mock_reporter):
    runner = LoadTestRunner(str(test_results_dir))
    runner.reporter = mock_reporter
    return runner

@pytest.fixture
def sample_test():
    class TestLoadTest(LoadTest):
        async def execute_request(self):
            await asyncio.sleep(0.1)
            return True
    
    return TestLoadTest("test_scenario")

@pytest.fixture
def sample_result():
    return LoadTestResult(
        name="test",
        total_requests=100,
        successful_requests=95,
        failed_requests=5,
        duration=10.0,
        avg_response_time=0.1,
        p95_response_time=0.2,
        p99_response_time=0.3
    )

@pytest.mark.asyncio
async def test_runner_initialization(runner, test_results_dir):
    assert runner.results_dir == Path(test_results_dir)
    assert runner.results_dir.exists()

@pytest.mark.asyncio
async def test_single_test_execution(runner, sample_test):
    result = await runner.run_test(sample_test)
    
    assert isinstance(result, LoadTestResult)
    assert result.name == "test_scenario"
    assert result.total_requests > 0

@pytest.mark.asyncio
async def test_test_suite_execution(runner):
    test_suite = [
        Mock(spec=LoadTest, name="test1"),
        Mock(spec=LoadTest, name="test2")
    ]
    
    for test in test_suite:
        test.run = AsyncMock(return_value=LoadTestResult(
            name=test.name,
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            duration=10.0,
            avg_response_time=0.1,
            p95_response_time=0.2,
            p99_response_time=0.3
        ))
    
    results = await runner.run_suite(test_suite)
    
    assert len(results) == 2
    assert all(isinstance(r, LoadTestResult) for r in results)

@pytest.mark.asyncio
async def test_result_persistence(runner, sample_result):
    # Test saving results
    await runner.save_result(sample_result)
    
    # Verify reporter was called
    runner.reporter.save_benchmark.assert_called_once()

@pytest.mark.asyncio
async def test_result_aggregation(runner):
    results = [
        LoadTestResult(
            name="test1",
            total_requests=100,
            successful_requests=90,
            failed_requests=10,
            duration=10.0,
            avg_response_time=0.1,
            p95_response_time=0.2,
            p99_response_time=0.3
        ),
        LoadTestResult(
            name="test2",
            total_requests=200,
            successful_requests=180,
            failed_requests=20,
            duration=10.0,
            avg_response_time=0.2,
            p95_response_time=0.3,
            p99_response_time=0.4
        )
    ]
    
    aggregated = runner.aggregate_results(results)
    
    assert aggregated.total_requests == 300
    assert aggregated.successful_requests == 270
    assert aggregated.failed_requests == 30
    assert aggregated.avg_response_time == 0.15

@pytest.mark.asyncio
async def test_error_handling(runner):
    failing_test = Mock(spec=LoadTest)
    failing_test.run = AsyncMock(side_effect=Exception("Test error"))
    
    with pytest.raises(Exception):
        await runner.run_test(failing_test)

@pytest.mark.asyncio
async def test_parallel_test_execution(runner):
    test_suite = [
        Mock(spec=LoadTest, name=f"test{i}") for i in range(3)
    ]
    
    for test in test_suite:
        test.run = AsyncMock(return_value=LoadTestResult(
            name=test.name,
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            duration=10.0,
            avg_response_time=0.1,
            p95_response_time=0.2,
            p99_response_time=0.3
        ))
    
    results = await runner.run_suite(test_suite, parallel=True)
    
    assert len(results) == 3
    assert all(isinstance(r, LoadTestResult) for r in results)

@pytest.mark.asyncio
async def test_result_comparison(runner):
    baseline_result = LoadTestResult(
        name="baseline",
        total_requests=100,
        successful_requests=95,
        failed_requests=5,
        duration=10.0,
        avg_response_time=0.1,
        p95_response_time=0.2,
        p99_response_time=0.3
    )
    
    current_result = LoadTestResult(
        name="current",
        total_requests=100,
        successful_requests=90,
        failed_requests=10,
        duration=10.0,
        avg_response_time=0.15,
        p95_response_time=0.25,
        p99_response_time=0.35
    )
    
    comparison = runner.compare_results(baseline_result, current_result)
    
    assert comparison["success_rate_change"] == -0.05
    assert comparison["response_time_change"] == 0.05

@pytest.mark.asyncio
async def test_cleanup(runner):
    # Setup some test artifacts
    test_file = runner.results_dir / "test.json"
    test_file.touch()
    
    await runner.cleanup(days_to_keep=0)
    
    assert not test_file.exists() 