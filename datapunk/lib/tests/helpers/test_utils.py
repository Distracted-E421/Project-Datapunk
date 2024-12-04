import asyncio
import functools
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from unittest.mock import MagicMock, patch

import pytest
from _pytest.fixtures import FixtureRequest

T = TypeVar('T')

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """Decorator to retry flaky tests."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

class AsyncMock(MagicMock):
    """Mock for async functions."""
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

def async_test(coro):
    """Decorator for async test functions."""
    @functools.wraps(coro)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper

class TimingContext:
    """Context manager for timing code execution."""
    def __init__(self, description: str = ""):
        self.description = description
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        if self.description:
            print(f"{self.description}: {self.duration:.4f} seconds")

@pytest.fixture
def benchmark_context(request: FixtureRequest):
    """Fixture for benchmarking code."""
    results: Dict[str, List[float]] = {}
    
    def record_benchmark(name: str, duration: float):
        if name not in results:
            results[name] = []
        results[name].append(duration)
    
    yield record_benchmark
    
    # Print benchmark results
    print("\nBenchmark Results:")
    for name, durations in results.items():
        avg_duration = sum(durations) / len(durations)
        print(f"{name}: avg={avg_duration:.4f}s over {len(durations)} runs")

@pytest.fixture
def mock_dependencies():
    """Fixture to mock common dependencies."""
    mocks = {
        'redis': AsyncMock(),
        'db': AsyncMock(),
        'cache': AsyncMock(),
        'logger': MagicMock(),
    }
    return mocks

def parametrize_with_cases(test_cases: List[Dict[str, Any]]):
    """Decorator to parametrize tests with named test cases."""
    ids = [case.get('id', f"case_{i}") for i, case in enumerate(test_cases)]
    return pytest.mark.parametrize("test_case", test_cases, ids=ids)

@pytest.fixture
def mock_config():
    """Fixture to provide test configuration."""
    return {
        'DEBUG': True,
        'TESTING': True,
        'REDIS_URL': 'redis://localhost:6379/0',
        'DB_URL': 'postgresql://localhost:5432/test',
    }

class TestDataBuilder:
    """Helper class to build test data."""
    def __init__(self):
        self.data: Dict[str, Any] = {}

    def with_field(self, name: str, value: Any) -> 'TestDataBuilder':
        self.data[name] = value
        return self

    def build(self) -> Dict[str, Any]:
        return self.data.copy()

@pytest.fixture
def test_data_builder():
    """Fixture to provide test data builder."""
    return TestDataBuilder()

def skip_in_ci():
    """Decorator to skip tests in CI environment."""
    return pytest.mark.skipif(
        "CI" in os.environ,
        reason="Test skipped in CI environment"
    )

@pytest.fixture
def mock_response_factory():
    """Fixture to create mock HTTP responses."""
    def create_response(
        status: int = 200,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ):
        response = MagicMock()
        response.status = status
        response.json = AsyncMock(return_value=json_data or {})
        response.headers = headers or {}
        return response
    return create_response

def assert_dict_contains_subset(subset: Dict, superset: Dict):
    """Assert that a dictionary contains a subset of key-value pairs."""
    for key, value in subset.items():
        assert key in superset
        assert superset[key] == value

@pytest.fixture
def cleanup_files():
    """Fixture to clean up test files."""
    created_files: List[str] = []
    
    def register_file(filepath: str):
        created_files.append(filepath)
    
    yield register_file
    
    # Cleanup
    for filepath in created_files:
        try:
            os.remove(filepath)
        except OSError:
            pass 