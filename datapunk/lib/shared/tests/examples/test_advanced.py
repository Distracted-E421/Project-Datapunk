import pytest
from ..helpers.test_utils import (
    retry_on_failure,
    AsyncMock,
    TimingContext,
    parametrize_with_cases,
    TestDataBuilder,
    assert_dict_contains_subset
)

# Example Service
class AdvancedService:
    def __init__(self, dependencies):
        self.redis = dependencies['redis']
        self.db = dependencies['db']
        self.logger = dependencies['logger']

    async def process_data(self, data):
        await self.redis.set('last_processed', data['id'])
        await self.db.save(data)
        self.logger.info(f"Processed data {data['id']}")
        return {'status': 'success', 'id': data['id']}

# Test Cases
test_cases = [
    {
        'id': 'valid_data',
        'input': {'id': '123', 'value': 'test'},
        'expected': {'status': 'success', 'id': '123'}
    },
    {
        'id': 'minimal_data',
        'input': {'id': '456'},
        'expected': {'status': 'success', 'id': '456'}
    }
]

# Flaky Test Example
@retry_on_failure(max_attempts=3)
def test_flaky_operation():
    """Example of handling flaky tests."""
    import random
    if random.random() < 0.5:  # Simulate occasional failures
        raise ValueError("Random failure")
    assert True

# Benchmark Test Example
@pytest.mark.benchmark
def test_performance_with_timing(benchmark_context):
    """Example of performance testing with timing."""
    with TimingContext() as timer:
        # Simulate work
        result = sum(range(1000000))
    
    benchmark_context("sum_operation", timer.duration)
    assert result > 0

# Parametrized Test Example
@pytest.mark.parametrize_with_cases(test_cases)
async def test_process_data(test_case, mock_dependencies):
    """Example of parametrized testing with mock dependencies."""
    service = AdvancedService(mock_dependencies)
    
    result = await service.process_data(test_case['input'])
    assert result == test_case['expected']
    
    # Verify mock calls
    mock_dependencies['redis'].set.assert_called_once_with(
        'last_processed', test_case['input']['id']
    )
    mock_dependencies['db'].save.assert_called_once_with(test_case['input'])

# Builder Pattern Test Example
def test_with_builder(test_data_builder):
    """Example of using builder pattern for test data."""
    data = (test_data_builder
            .with_field('id', '789')
            .with_field('name', 'test')
            .with_field('timestamp', '2024-01-01')
            .build())
    
    assert data['id'] == '789'
    assert data['name'] == 'test'
    assert data['timestamp'] == '2024-01-01'

# Mock Response Test Example
@pytest.mark.asyncio
async def test_http_client(mock_response_factory):
    """Example of testing HTTP responses."""
    mock_response = mock_response_factory(
        status=200,
        json_data={'status': 'ok'},
        headers={'Content-Type': 'application/json'}
    )
    
    assert mock_response.status == 200
    assert await mock_response.json() == {'status': 'ok'}
    assert mock_response.headers['Content-Type'] == 'application/json'

# Cleanup Test Example
def test_file_cleanup(cleanup_files, tmp_path):
    """Example of automatic file cleanup."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    cleanup_files(str(test_file))
    # File will be automatically cleaned up after test

# Dict Assertion Example
def test_dict_assertion():
    """Example of advanced dictionary assertions."""
    full_data = {
        'id': '123',
        'name': 'test',
        'timestamp': '2024-01-01',
        'extra': 'not important'
    }
    
    expected_subset = {
        'id': '123',
        'name': 'test'
    }
    
    assert_dict_contains_subset(expected_subset, full_data)

# Integration Test Example
@pytest.mark.integration
async def test_integration_with_redis(redis_client, cleanup_redis):
    """Example of integration testing with Redis."""
    test_key = 'test:integration'
    test_value = 'integration_value'
    
    await redis_client.set(test_key, test_value)
    result = await redis_client.get(test_key)
    
    assert result == test_value
    # cleanup_redis will automatically clean up after test

if __name__ == '__main__':
    pytest.main(['-v', __file__]) 