import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from datapunk_shared.error.error_types import (
    ServiceError, ErrorContext, ErrorCategory, ErrorSeverity
)
from datapunk_shared.error.handlers import ErrorHandlers
from datapunk_shared.error.recovery_strategies import RecoveryStrategies, RetryConfig

@pytest.fixture
def mock_logger():
    return Mock(
        info=Mock(),
        error=Mock(),
        warning=Mock()
    )

@pytest.fixture
def mock_circuit_breaker():
    return Mock(
        is_allowed=Mock(return_value=True)
    )

@pytest.fixture
def mock_auth_service():
    return AsyncMock(
        refresh_token=AsyncMock(return_value="new_token")
    )

@pytest.fixture
def mock_db_manager():
    return AsyncMock(
        reset_connections=AsyncMock()
    )

@pytest.fixture
def mock_resource_manager():
    return AsyncMock(
        optimize_resources=AsyncMock(),
        cleanup_resources=AsyncMock()
    )

@pytest.fixture
def error_handlers(mock_circuit_breaker):
    recovery = RecoveryStrategies(RetryConfig())
    return ErrorHandlers(recovery, mock_circuit_breaker)

@pytest.fixture
def sample_error_context():
    return ErrorContext(
        service_id="test_service",
        operation="test_operation",
        trace_id="test_trace",
        timestamp=datetime.now().timestamp(),
        additional_data={}
    )

class TestErrorHandlers:
    @pytest.mark.asyncio
    async def test_handle_authentication_error_with_token_refresh(
        self,
        error_handlers,
        mock_auth_service,
        sample_error_context
    ):
        # Setup
        sample_error_context.additional_data = {
            'token_expired': True,
            'refresh_token': 'old_token'
        }
        error = ServiceError(
            code="AUTH_ERROR",
            message="Token expired",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.WARNING,
            context=sample_error_context
        )

        # Execute
        result = await error_handlers.handle_authentication_error(error, mock_auth_service)

        # Verify
        assert result is not None
        assert result['status'] == 'retry'
        assert result['new_token'] == 'new_token'
        mock_auth_service.refresh_token.assert_called_once_with('old_token')

    @pytest.mark.asyncio
    async def test_handle_database_error_with_connection_reset(
        self,
        error_handlers,
        mock_db_manager,
        sample_error_context
    ):
        # Setup
        error = ServiceError(
            code="DB_ERROR",
            message="connection lost",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.ERROR,
            context=sample_error_context
        )
        operation = AsyncMock(return_value={'status': 'success'})

        # Execute
        result = await error_handlers.handle_database_error(
            error,
            mock_db_manager,
            operation
        )

        # Verify
        assert result == {'status': 'success'}
        mock_db_manager.reset_connections.assert_called_once()
        operation.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_rate_limit_error(
        self,
        error_handlers,
        sample_error_context
    ):
        # Setup
        sample_error_context.additional_data = {'retry_after': 30}
        error = ServiceError(
            code="RATE_LIMIT",
            message="Too many requests",
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.WARNING,
            context=sample_error_context
        )

        # Execute
        result = await error_handlers.handle_rate_limit_error(error)

        # Verify
        assert result['status'] == 'rate_limited'
        assert result['retry_after'] == 30

    @pytest.mark.asyncio
    async def test_handle_network_error_with_circuit_breaker(
        self,
        error_handlers,
        mock_circuit_breaker,
        sample_error_context
    ):
        # Setup
        error = ServiceError(
            code="NETWORK_ERROR",
            message="Connection refused",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.ERROR,
            context=sample_error_context
        )
        operation = AsyncMock(return_value={'status': 'success'})
        mock_circuit_breaker.is_allowed.return_value = False

        # Execute
        result = await error_handlers.handle_network_error(error, operation)

        # Verify
        assert result['status'] == 'circuit_open'
        operation.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_resource_error_with_cleanup(
        self,
        error_handlers,
        mock_resource_manager,
        sample_error_context
    ):
        # Setup
        error = ServiceError(
            code="RESOURCE_ERROR",
            message="insufficient resources",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.ERROR,
            context=sample_error_context
        )
        operation = AsyncMock(return_value={'status': 'success'})

        # Execute
        result = await error_handlers.handle_resource_error(
            error,
            mock_resource_manager,
            operation
        )

        # Verify
        assert result == {'status': 'success'}
        mock_resource_manager.optimize_resources.assert_called_once()
        mock_resource_manager.cleanup_resources.assert_called_once() 