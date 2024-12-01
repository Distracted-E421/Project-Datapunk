import pytest
import asyncio
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import tempfile
import os

from src.ingestion.core import DataSource
from src.ingestion.source_handlers import (
    HandlerFactory,
    StructuredDataHandler,
    UnstructuredDataHandler,
    StreamDataHandler
)

# Test Data
SAMPLE_JSON = {
    "id": "test1",
    "value": 42,
    "tags": ["sample", "test"]
}

SAMPLE_CSV_DATA = """
id,value,tags
test1,42,"sample,test"
test2,43,"sample,production"
"""

SAMPLE_TEXT = "This is a sample text document for testing."
SAMPLE_BINARY = b"Binary data for testing"

# Fixtures
@pytest.fixture
def structured_config():
    return {
        "format": "json",
        "schema": "test_schema"
    }

@pytest.fixture
def unstructured_config():
    return {
        "type": "text",
        "max_size": 1024 * 1024  # 1MB
    }

@pytest.fixture
def stream_config():
    return {
        "type": "kafka",
        "buffer_size": 100,
        "flush_interval": 5
    }

@pytest.fixture
async def temp_json_file():
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as f:
        json.dump(SAMPLE_JSON, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
async def temp_csv_file():
    with tempfile.NamedTemporaryFile(suffix='.csv', mode='w', delete=False) as f:
        f.write(SAMPLE_CSV_DATA)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

# Factory Tests
@pytest.mark.asyncio
async def test_handler_factory_structured(structured_config):
    handler = await HandlerFactory.create_handler(DataSource.STRUCTURED, structured_config)
    assert isinstance(handler, StructuredDataHandler)

@pytest.mark.asyncio
async def test_handler_factory_invalid_config():
    with pytest.raises(ValueError):
        await HandlerFactory.create_handler(DataSource.STRUCTURED, {})

# Structured Data Handler Tests
@pytest.mark.asyncio
async def test_structured_handler_dict(structured_config):
    handler = StructuredDataHandler(structured_config)
    result = await handler.process(SAMPLE_JSON)
    
    assert result["data"] == SAMPLE_JSON
    assert result["metadata"]["source_type"] == "structured"
    assert result["metadata"]["format"] == "dict"

@pytest.mark.asyncio
async def test_structured_handler_json_file(structured_config, temp_json_file):
    handler = StructuredDataHandler(structured_config)
    result = await handler.process(temp_json_file)
    
    assert result["data"] == SAMPLE_JSON
    assert result["metadata"]["source_type"] == "structured"

@pytest.mark.asyncio
async def test_structured_handler_pandas(structured_config):
    df = pd.DataFrame([SAMPLE_JSON])
    handler = StructuredDataHandler(structured_config)
    result = await handler.process(df)
    
    assert isinstance(result["data"], list)
    assert result["metadata"]["format"] == "pandas"
    assert result["metadata"]["shape"] == df.shape

# Unstructured Data Handler Tests
@pytest.mark.asyncio
async def test_unstructured_handler_text(unstructured_config):
    handler = UnstructuredDataHandler(unstructured_config)
    result = await handler.process(SAMPLE_TEXT)
    
    assert result["data"] == SAMPLE_TEXT
    assert result["metadata"]["source_type"] == "unstructured"
    assert result["metadata"]["format"] == "text"
    assert result["metadata"]["length"] == len(SAMPLE_TEXT)

@pytest.mark.asyncio
async def test_unstructured_handler_binary(unstructured_config):
    handler = UnstructuredDataHandler(unstructured_config)
    result = await handler.process(SAMPLE_BINARY)
    
    assert result["data"] == SAMPLE_BINARY
    assert result["metadata"]["source_type"] == "unstructured"
    assert result["metadata"]["format"] == "binary"
    assert result["metadata"]["size"] == len(SAMPLE_BINARY)

# Stream Data Handler Tests
@pytest.mark.asyncio
async def test_stream_handler_json(stream_config):
    handler = StreamDataHandler(stream_config)
    await handler.start()
    
    result = await handler.process(json.dumps(SAMPLE_JSON).encode())
    
    assert result["data"] == SAMPLE_JSON
    assert result["metadata"]["source_type"] == "stream"
    assert "sequence" in result["metadata"]
    
    await handler.stop()

@pytest.mark.asyncio
async def test_stream_handler_binary(stream_config):
    handler = StreamDataHandler(stream_config)
    await handler.start()
    
    result = await handler.process(SAMPLE_BINARY)
    
    assert result["data"] == SAMPLE_BINARY
    assert result["metadata"]["source_type"] == "stream"
    assert result["metadata"]["format"] == "binary"
    
    await handler.stop()

@pytest.mark.asyncio
async def test_stream_handler_buffer(stream_config):
    # Set small buffer for testing
    stream_config["buffer_size"] = 2
    handler = StreamDataHandler(stream_config)
    await handler.start()
    
    # Process multiple messages
    for _ in range(3):
        await handler.process(SAMPLE_JSON)
    
    # Buffer should have been flushed at least once
    assert len(handler.buffer) < 3
    
    await handler.stop()

@pytest.mark.asyncio
async def test_stream_handler_periodic_flush(stream_config):
    # Set short flush interval for testing
    stream_config["flush_interval"] = 0.1
    handler = StreamDataHandler(stream_config)
    await handler.start()
    
    # Add some data
    await handler.process(SAMPLE_JSON)
    
    # Wait for periodic flush
    await asyncio.sleep(0.2)
    
    # Buffer should be empty after flush
    assert len(handler.buffer) == 0
    
    await handler.stop()

# Error Handling Tests
@pytest.mark.asyncio
async def test_structured_handler_invalid_file(structured_config):
    handler = StructuredDataHandler(structured_config)
    with pytest.raises(FileNotFoundError):
        await handler.process("nonexistent.json")

@pytest.mark.asyncio
async def test_structured_handler_invalid_type(structured_config):
    handler = StructuredDataHandler(structured_config)
    with pytest.raises(ValueError):
        await handler.process(123)  # Invalid type

@pytest.mark.asyncio
async def test_unstructured_handler_invalid_type(unstructured_config):
    handler = UnstructuredDataHandler(unstructured_config)
    with pytest.raises(ValueError):
        await handler.process(123)  # Invalid type

# Integration Tests
@pytest.mark.asyncio
async def test_handler_integration():
    # Test processing the same data through different handlers
    data = json.dumps(SAMPLE_JSON).encode()
    
    # Process as structured data
    structured_handler = await HandlerFactory.create_handler(
        DataSource.STRUCTURED,
        {"format": "json", "schema": "test"}
    )
    structured_result = await structured_handler.process(json.loads(data))
    
    # Process as unstructured data
    unstructured_handler = await HandlerFactory.create_handler(
        DataSource.UNSTRUCTURED,
        {"type": "binary", "max_size": 1024}
    )
    unstructured_result = await unstructured_handler.process(data)
    
    # Process as stream data
    stream_handler = await HandlerFactory.create_handler(
        DataSource.STREAM,
        {"type": "test", "buffer_size": 100, "flush_interval": 5}
    )
    await stream_handler.start()
    stream_result = await stream_handler.process(data)
    await stream_handler.stop()
    
    # Verify each handler processed the data appropriately
    assert structured_result["metadata"]["source_type"] == "structured"
    assert unstructured_result["metadata"]["source_type"] == "unstructured"
    assert stream_result["metadata"]["source_type"] == "stream" 