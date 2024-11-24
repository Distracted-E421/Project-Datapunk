import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from datapunk_shared.error.error_types import (
    ServiceError, ErrorContext, ErrorCategory, ErrorSeverity
)
from datapunk_shared.error.recovery_strategies import RecoveryStrategies, RetryConfig

@pytest.fixture
def sample_error_context():
    return ErrorContext(
        service_id="test_service",
        operation="test_operation",
        trace_id="test_trace",
        timestamp=datetime.now().timestamp()
    )

@pytest.fixture
def recovery_strategies():
    return RecoveryStrategies(
        RetryConfig(
            initial_delay=0.1,
            max_delay=1.0,
            exponential_base=2,
            jitter=False
        )
    )

class TestRecoveryStrategies:
    @pytest.mark.asyncio
    async def test_network_recovery_successful(
        self,
        recovery_strategies,
        sample_error_context
    ):
        # Setup
        error = ServiceError(
            code="NETWORK_ERROR",
            message="Connection reset",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.ERROR,
            context=sample_error_context
        )
        operation = AsyncMock(return_value={'status': 'success'})

        # Execute
        result = await recovery_strategies.network_recovery(error, 1, operation)

        # Verify
        assert result == {'status': 'success'}
        operation.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_recovery_with_fallback(
        self,
        recovery_strategies,
        sample_error_context
    ):
        # Setup
        error = ServiceError(
            code="CACHE_ERROR",
            message="Cache miss",
            category=ErrorCategory.CACHE,
            severity=ErrorSeverity.WARNING,
            context=sample_error_context
        )
        fallback = AsyncMock(return_value={'data': 'from_source'})

        # Execute
        result = await recovery_strategies.cache_recovery(error, 1, fallback)

        # Verify
        assert result == {'data': 'from_source'}
        fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_recovery_with_connection_reset(
        self,
        recovery_strategies,
        sample_error_context
    ):
        # Setup
        error = ServiceError(
            code="DB_ERROR",
            message="Connection lost",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR,
            context=sample_error_context
        )
        operation = AsyncMock(return_value={'status': 'success'})
        connection_manager = AsyncMock(reset_connections=AsyncMock())

        # Execute
        result = await recovery_strategies.database_recovery(
            error,
            1,
            operation,
            connection_manager
        )

        # Verify
        assert result == {'status': 'success'}
        connection_manager.reset_connections.assert_called_once()
        operation.assert_called_once()

    @pytest.mark.asyncio
    async def test_resource_recovery_with_cleanup(
        self,
        recovery_strategies,
        sample_error_context
    ):
        # Setup
        error = ServiceError(
            code="RESOURCE_ERROR",
            message="Resource exhausted",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.ERROR,
            context=sample_error_context
        )
        operation = AsyncMock(return_value={'status': 'success'})
        resource_manager = AsyncMock(cleanup_resources=AsyncMock())

        # Execute
        result = await recovery_strategies.resource_recovery(
            error,
            1,
            operation,
            resource_manager
        )

        # Verify
        assert result == {'status': 'success'}
        resource_manager.cleanup_resources.assert_called_once()
        operation.assert_called_once()

    def test_calculate_backoff(self, recovery_strategies):
        # Test initial delay
        assert recovery_strategies._calculate_backoff(1) == 0.1
        
        # Test exponential increase
        assert recovery_strategies._calculate_backoff(2) == 0.2
        assert recovery_strategies._calculate_backoff(3) == 0.4
        
        # Test max delay
        assert recovery_strategies._calculate_backoff(5) == 1.0 