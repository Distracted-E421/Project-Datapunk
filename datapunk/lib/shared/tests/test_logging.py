import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import logging
from datapunk_shared.logging import (
    LogManager,
    LogConfig,
    LogHandler,
    LogFormatter,
    LogLevel,
    LogError
)

@pytest.fixture
def log_config():
    return LogConfig(
        name="test_logger",
        level=LogLevel.INFO,
        handlers=[
            LogHandler(
                name="console",
                type="stream",
                level=LogLevel.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            LogHandler(
                name="file",
                type="file",
                level=LogLevel.DEBUG,
                filename="test.log",
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                max_bytes=1024 * 1024,  # 1MB
                backup_count=5
            )
        ],
        metrics_enabled=True
    )

@pytest.fixture
async def log_manager(log_config):
    manager = LogManager(log_config)
    await manager.initialize()
    return manager

@pytest.mark.asyncio
async def test_manager_initialization(log_manager, log_config):
    """Test log manager initialization"""
    assert log_manager.config == log_config
    assert log_manager.is_initialized
    assert len(log_manager.handlers) == len(log_config.handlers)

@pytest.mark.asyncio
async def test_console_logging(log_manager):
    """Test console logging"""
    with patch('sys.stdout') as mock_stdout:
        await log_manager.log(
            level=LogLevel.INFO,
            message="Test message",
            module="test_module"
        )
        
        mock_stdout.write.assert_called()

@pytest.mark.asyncio
async def test_file_logging(log_manager):
    """Test file logging"""
    with patch('builtins.open', MagicMock()):
        await log_manager.log(
            level=LogLevel.DEBUG,
            message="Debug message",
            module="test_module"
        )
        
        # Verify file was written
        open.assert_called()

@pytest.mark.asyncio
async def test_log_levels(log_manager):
    """Test different log levels"""
    messages = []
    
    # Mock handler
    class MockHandler:
        def emit(self, record):
            messages.append((record.levelname, record.message))
    
    log_manager.add_handler("mock", MockHandler())
    
    # Test all levels
    await log_manager.debug("Debug message")
    await log_manager.info("Info message")
    await log_manager.warning("Warning message")
    await log_manager.error("Error message")
    await log_manager.critical("Critical message")
    
    assert len(messages) == 5
    assert any(m[0] == "DEBUG" for m in messages)
    assert any(m[0] == "CRITICAL" for m in messages)

@pytest.mark.asyncio
async def test_log_formatting(log_manager):
    """Test log formatting"""
    formatted_messages = []
    
    class MockFormatter(LogFormatter):
        def format(self, record):
            formatted_messages.append(record)
            return super().format(record)
    
    log_manager.set_formatter("console", MockFormatter())
    
    await log_manager.info(
        "Test message",
        extra={
            "user_id": "123",
            "request_id": "abc"
        }
    )
    
    assert len(formatted_messages) > 0
    assert hasattr(formatted_messages[0], "user_id")
    assert hasattr(formatted_messages[0], "request_id")

@pytest.mark.asyncio
async def test_log_filtering(log_manager):
    """Test log filtering"""
    filtered_messages = []
    
    def log_filter(record):
        if record.module == "test_module":
            filtered_messages.append(record)
            return True
        return False
    
    log_manager.add_filter("module_filter", log_filter)
    
    # Should be filtered
    await log_manager.info(
        "Test message",
        module="test_module"
    )
    
    # Should not be filtered
    await log_manager.info(
        "Another message",
        module="other_module"
    )
    
    assert len(filtered_messages) == 1
    assert filtered_messages[0].module == "test_module"

@pytest.mark.asyncio
async def test_log_metrics(log_manager):
    """Test log metrics collection"""
    metrics = []
    log_manager.set_metrics_callback(metrics.append)
    
    await log_manager.info("Test message")
    
    assert len(metrics) > 0
    assert any(m["type"] == "log_entry" for m in metrics)
    assert any(m["level"] == "INFO" for m in metrics)

@pytest.mark.asyncio
async def test_structured_logging(log_manager):
    """Test structured logging"""
    structured_logs = []
    
    class StructuredHandler(LogHandler):
        def emit(self, record):
            structured_logs.append({
                "timestamp": record.created,
                "level": record.levelname,
                "message": record.message,
                "context": getattr(record, "context", {})
            })
    
    log_manager.add_handler("structured", StructuredHandler())
    
    await log_manager.info(
        "Structured message",
        context={
            "user_id": "123",
            "action": "login",
            "status": "success"
        }
    )
    
    assert len(structured_logs) > 0
    assert "context" in structured_logs[0]
    assert structured_logs[0]["context"]["user_id"] == "123"

@pytest.mark.asyncio
async def test_error_handling(log_manager):
    """Test error handling"""
    # Test with invalid log level
    with pytest.raises(LogError):
        await log_manager.log(
            level="INVALID_LEVEL",
            message="Test message"
        )
    
    # Test with invalid handler
    with pytest.raises(LogError):
        log_manager.add_handler(
            "invalid",
            None
        )

@pytest.mark.asyncio
async def test_log_rotation(log_manager):
    """Test log file rotation"""
    with patch('logging.handlers.RotatingFileHandler') as mock_handler:
        # Simulate file size exceeding max_bytes
        mock_handler.return_value.shouldRollover.return_value = True
        
        for _ in range(100):
            await log_manager.info("Test message" * 100)
        
        # Verify rotation occurred
        mock_handler.return_value.doRollover.assert_called()

@pytest.mark.asyncio
async def test_context_logging(log_manager):
    """Test logging with context manager"""
    logs = []
    
    class ContextHandler(LogHandler):
        def emit(self, record):
            logs.append(record)
    
    log_manager.add_handler("context", ContextHandler())
    
    async with log_manager.context(user_id="123", session_id="abc"):
        await log_manager.info("Test message")
        
        # Nested context
        async with log_manager.context(request_id="xyz"):
            await log_manager.info("Nested message")
    
    assert len(logs) == 2
    assert hasattr(logs[0], "user_id")
    assert hasattr(logs[1], "request_id")

@pytest.mark.asyncio
async def test_async_logging(log_manager):
    """Test asynchronous logging"""
    async_logs = []
    
    class AsyncHandler(LogHandler):
        async def async_emit(self, record):
            async_logs.append(record)
    
    log_manager.add_handler("async", AsyncHandler())
    
    # Test batch logging
    await asyncio.gather(*[
        log_manager.info(f"Message {i}")
        for i in range(10)
    ])
    
    assert len(async_logs) == 10
    assert all(isinstance(log, logging.LogRecord) for log in async_logs)

@pytest.mark.asyncio
async def test_log_sampling(log_manager):
    """Test log sampling"""
    sampled_logs = []
    
    def sample_filter(record):
        if getattr(record, "sample_rate", 1.0) >= 0.5:
            sampled_logs.append(record)
            return True
        return False
    
    log_manager.add_filter("sampler", sample_filter)
    
    # Log with different sample rates
    await log_manager.info("High priority", sample_rate=1.0)
    await log_manager.info("Medium priority", sample_rate=0.5)
    await log_manager.info("Low priority", sample_rate=0.1)
    
    assert len(sampled_logs) == 2  # High and medium priority