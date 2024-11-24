import pytest
import asyncio
from unittest.mock import Mock, patch
from datapunk_shared.mesh.retry import RetryPolicy, RetryConfig, with_retry

@pytest.fixture
def retry_policy():
    return RetryPolicy(RetryConfig(
        max_attempts=3,
        initial_delay=0.01,
        max_delay=0.1,
        jitter=False
    ))

class TestRetryPolicy:
    @pytest.mark.asyncio
    async def test_successful_operation(self, retry_policy):
        """Test successful operation without retries."""
        mock_operation = Mock(return_value=asyncio.Future())
        mock_operation.return_value.set_result("success")
        
        result = await retry_policy.execute_with_retry(
            mock_operation,
            service_name="test",
            operation_name="test_op"
        )
        
        assert result == "success"
        assert mock_operation.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_with_eventual_success(self, retry_policy):
        """Test operation that succeeds after retries."""
        mock_operation = Mock(side_effect=[
            Exception("First failure"),
            Exception("Second failure"),
            "success"
        ])
        
        result = await retry_policy.execute_with_retry(
            mock_operation,
            service_name="test",
            operation_name="test_op"
        )
        
        assert result == "success"
        assert mock_operation.call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, retry_policy):
        """Test operation that fails all retry attempts."""
        mock_operation = Mock(side_effect=Exception("Persistent failure"))
        
        with pytest.raises(Exception) as exc_info:
            await retry_policy.execute_with_retry(
                mock_operation,
                service_name="test",
                operation_name="test_op"
            )
        
        assert str(exc_info.value) == "Persistent failure"
        assert mock_operation.call_count == retry_policy.config.max_attempts

    @pytest.mark.asyncio
    async def test_retry_decorator(self):
        """Test retry decorator functionality."""
        mock_counter = Mock(return_value=0)
        
        @with_retry(
            retry_config=RetryConfig(max_attempts=3, initial_delay=0.01),
            service_name="test"
        )
        async def test_operation():
            mock_counter.return_value += 1
            if mock_counter.return_value < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = await test_operation()
        assert result == "success"
        assert mock_counter.return_value == 2

    def test_delay_calculation(self, retry_policy):
        """Test exponential backoff delay calculation."""
        delays = [
            retry_policy.calculate_delay(attempt)
            for attempt in range(5)
        ]
        
        # Verify exponential growth
        for i in range(1, len(delays)):
            assert delays[i] > delays[i-1]
            
        # Verify max delay cap
        assert all(delay <= retry_policy.config.max_delay for delay in delays) 