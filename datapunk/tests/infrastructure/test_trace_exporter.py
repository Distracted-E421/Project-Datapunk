import pytest
import asyncio
import json
import os
import aiohttp
from datetime import datetime
from unittest.mock import patch, MagicMock
from datapunk.lib.tracing.tracer import (
    SpanKind, SpanContext, Span
)
from src.infrastructure.trace_exporter import (
    ExporterConfig, ConsoleExporter, JsonFileExporter,
    HttpExporter, BatchSpanProcessor
)

@pytest.fixture
def test_span():
    context = SpanContext(
        trace_id="test-trace-id",
        span_id="test-span-id"
    )
    return Span(
        name="test_span",
        context=context,
        kind=SpanKind.INTERNAL,
        start_time=datetime.now()
    )

@pytest.fixture
def test_spans(test_span):
    return [test_span]

@pytest.fixture
def exporter_config():
    return ExporterConfig(
        endpoint="http://test.endpoint/traces",
        api_key="test-api-key",
        batch_size=2,
        flush_interval=0.1
    )

@pytest.mark.asyncio
async def test_console_exporter(test_spans, caplog):
    exporter = ConsoleExporter()
    success = await exporter.export(test_spans)
    
    assert success is True
    assert "test_span" in caplog.text
    assert "test-trace-id" in caplog.text

@pytest.mark.asyncio
async def test_json_file_exporter(test_spans, tmp_path):
    filepath = tmp_path / "traces.jsonl"
    exporter = JsonFileExporter(str(filepath))
    
    success = await exporter.export(test_spans)
    assert success is True
    assert filepath.exists()
    
    # Verify file contents
    with open(filepath) as f:
        data = json.loads(f.readline())
        assert data["trace_id"] == "test-trace-id"
        assert data["span_id"] == "test-span-id"
        assert data["name"] == "test_span"

@pytest.mark.asyncio
async def test_json_file_exporter_error(test_spans, tmp_path):
    # Test with invalid filepath
    exporter = JsonFileExporter("/invalid/path/traces.jsonl")
    success = await exporter.export(test_spans)
    assert success is False

class MockResponse:
    def __init__(self, status: int, text: str = ""):
        self.status = status
        self._text = text
    
    async def text(self):
        return self._text
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_http_exporter_success(test_spans, exporter_config):
    exporter = HttpExporter(exporter_config)
    
    # Mock successful response
    mock_response = MockResponse(200)
    mock_session = MagicMock()
    mock_session.post.return_value = mock_response
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        success = await exporter.export(test_spans)
        assert success is True
        
        # Verify request
        mock_session.post.assert_called_once()
        args, kwargs = mock_session.post.call_args
        assert args[0] == exporter_config.endpoint
        assert "spans" in kwargs["json"]
        assert len(kwargs["json"]["spans"]) == 1
        
        await exporter.close()

@pytest.mark.asyncio
async def test_http_exporter_retry(test_spans, exporter_config):
    exporter = HttpExporter(exporter_config)
    
    # Mock responses: two failures followed by success
    responses = [
        MockResponse(500, "Server Error"),
        MockResponse(503, "Service Unavailable"),
        MockResponse(200)
    ]
    
    mock_session = MagicMock()
    mock_session.post = MagicMock(side_effect=responses)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        success = await exporter.export(test_spans)
        assert success is True
        assert mock_session.post.call_count == 3
        
        await exporter.close()

@pytest.mark.asyncio
async def test_http_exporter_failure(test_spans, exporter_config):
    exporter = HttpExporter(exporter_config)
    
    # Mock all failures
    mock_response = MockResponse(500, "Server Error")
    mock_session = MagicMock()
    mock_session.post.return_value = mock_response
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        success = await exporter.export(test_spans)
        assert success is False
        assert mock_session.post.call_count == exporter_config.retry_count
        
        await exporter.close()

@pytest.mark.asyncio
async def test_batch_processor(test_spans, exporter_config):
    mock_exporter = MagicMock()
    mock_exporter.export = AsyncMock(return_value=True)
    
    processor = BatchSpanProcessor(mock_exporter, exporter_config)
    await processor.start()
    
    # Add spans
    for span in test_spans:
        processor.on_end(span)
    
    # Wait for flush interval
    await asyncio.sleep(exporter_config.flush_interval * 1.1)
    
    # Verify export was called
    mock_exporter.export.assert_called_once()
    exported_spans = mock_exporter.export.call_args[0][0]
    assert len(exported_spans) == len(test_spans)
    
    await processor.shutdown()

@pytest.mark.asyncio
async def test_batch_processor_batch_size(test_spans, exporter_config):
    mock_exporter = MagicMock()
    mock_exporter.export = AsyncMock(return_value=True)
    
    # Set small batch size
    exporter_config.batch_size = 1
    processor = BatchSpanProcessor(mock_exporter, exporter_config)
    
    # Add multiple spans
    for span in test_spans * 2:  # Double the spans
        processor.on_end(span)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    # Verify immediate export due to batch size
    assert mock_exporter.export.called
    
    await processor.shutdown()

@pytest.mark.asyncio
async def test_batch_processor_shutdown(test_spans, exporter_config):
    mock_exporter = MagicMock()
    mock_exporter.export = AsyncMock(return_value=True)
    
    processor = BatchSpanProcessor(mock_exporter, exporter_config)
    await processor.start()
    
    # Add spans but don't wait for flush interval
    for span in test_spans:
        processor.on_end(span)
    
    # Shutdown should export remaining spans
    await processor.shutdown()
    
    assert mock_exporter.export.called
    exported_spans = mock_exporter.export.call_args[0][0]
    assert len(exported_spans) == len(test_spans)

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

@pytest.mark.asyncio
async def test_batch_processor_export_failure(test_spans, exporter_config):
    mock_exporter = MagicMock()
    mock_exporter.export = AsyncMock(return_value=False)
    
    processor = BatchSpanProcessor(mock_exporter, exporter_config)
    await processor.start()
    
    # Add spans
    for span in test_spans:
        processor.on_end(span)
    
    # Wait for flush interval
    await asyncio.sleep(exporter_config.flush_interval * 1.1)
    
    # Verify export was attempted
    assert mock_exporter.export.called
    
    await processor.shutdown() 