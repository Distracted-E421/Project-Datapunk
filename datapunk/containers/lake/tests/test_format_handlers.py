import pytest
import json
import yaml
import pandas as pd
import numpy as np
from datetime import datetime
import tempfile
import os
from pathlib import Path
import avro.schema
from avro.io import DatumWriter, BinaryEncoder
import io

from src.ingestion.monitoring import MetricCollector, HandlerMetrics
from src.ingestion.format_handlers import (
    FormatHandlerFactory,
    JSONHandler,
    YAMLHandler,
    XMLHandler,
    CSVHandler,
    AvroHandler,
    ParquetHandler
)

# Test Data
SAMPLE_JSON = {
    "id": "test1",
    "value": 42,
    "nested": {
        "key": "value"
    }
}

SAMPLE_YAML = """
id: test1
value: 42
nested:
  key: value
"""

SAMPLE_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<root>
    <id>test1</id>
    <value>42</value>
    <nested>
        <key>value</key>
    </nested>
</root>
"""

SAMPLE_CSV = """
id,value,key
test1,42,value
test2,43,value2
"""

AVRO_SCHEMA = {
    "type": "record",
    "name": "test",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "value", "type": "int"},
        {"name": "key", "type": "string"}
    ]
}

# Fixtures
@pytest.fixture
async def metric_collector():
    collector = MetricCollector()
    await collector.start()
    yield collector
    await collector.stop()

@pytest.fixture
def handler_metrics(metric_collector):
    return HandlerMetrics(metric_collector)

@pytest.fixture
def handler_factory(handler_metrics):
    return FormatHandlerFactory(handler_metrics)

@pytest.fixture
def avro_data():
    schema = avro.schema.parse(json.dumps(AVRO_SCHEMA))
    writer = DatumWriter(schema)
    bytes_io = io.BytesIO()
    encoder = BinaryEncoder(bytes_io)
    writer.write({"id": "test1", "value": 42, "key": "value"}, encoder)
    return bytes_io.getvalue()

# Factory Tests
@pytest.mark.asyncio
async def test_handler_factory_creation(handler_factory):
    handlers = [
        await handler_factory.create_handler("json"),
        await handler_factory.create_handler("yaml"),
        await handler_factory.create_handler("xml"),
        await handler_factory.create_handler("csv")
    ]
    
    assert isinstance(handlers[0], JSONHandler)
    assert isinstance(handlers[1], YAMLHandler)
    assert isinstance(handlers[2], XMLHandler)
    assert isinstance(handlers[3], CSVHandler)

@pytest.mark.asyncio
async def test_handler_factory_invalid_format(handler_factory):
    with pytest.raises(ValueError):
        await handler_factory.create_handler("invalid_format")

# JSON Handler Tests
@pytest.mark.asyncio
async def test_json_handler_string(handler_factory):
    handler = await handler_factory.create_handler("json")
    result = await handler.process(json.dumps(SAMPLE_JSON))
    assert result == SAMPLE_JSON

@pytest.mark.asyncio
async def test_json_handler_dict(handler_factory):
    handler = await handler_factory.create_handler("json")
    result = await handler.process(SAMPLE_JSON)
    assert result == SAMPLE_JSON

@pytest.mark.asyncio
async def test_json_handler_invalid(handler_factory):
    handler = await handler_factory.create_handler("json")
    with pytest.raises(ValueError):
        await handler.process("invalid json")

# YAML Handler Tests
@pytest.mark.asyncio
async def test_yaml_handler(handler_factory):
    handler = await handler_factory.create_handler("yaml")
    result = await handler.process(SAMPLE_YAML)
    assert result["id"] == "test1"
    assert result["value"] == 42
    assert result["nested"]["key"] == "value"

@pytest.mark.asyncio
async def test_yaml_handler_invalid(handler_factory):
    handler = await handler_factory.create_handler("yaml")
    with pytest.raises(ValueError):
        await handler.process("invalid: yaml: :")

# XML Handler Tests
@pytest.mark.asyncio
async def test_xml_handler(handler_factory):
    handler = await handler_factory.create_handler("xml")
    result = await handler.process(SAMPLE_XML)
    assert result["root"]["id"] == "test1"
    assert result["root"]["value"] == "42"
    assert result["root"]["nested"]["key"] == "value"

@pytest.mark.asyncio
async def test_xml_handler_invalid(handler_factory):
    handler = await handler_factory.create_handler("xml")
    with pytest.raises(ValueError):
        await handler.process("<invalid>xml<invalid>")

# CSV Handler Tests
@pytest.mark.asyncio
async def test_csv_handler(handler_factory):
    handler = await handler_factory.create_handler("csv")
    result = await handler.process(SAMPLE_CSV)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == "test1"
    assert result[0]["value"] == 42

@pytest.mark.asyncio
async def test_csv_handler_with_options(handler_factory):
    handler = await handler_factory.create_handler(
        "csv",
        dtype={"value": int}
    )
    result = await handler.process(SAMPLE_CSV)
    assert isinstance(result[0]["value"], int)

# Avro Handler Tests
@pytest.mark.asyncio
async def test_avro_handler(handler_factory, avro_data):
    handler = await handler_factory.create_handler(
        "avro",
        schema=AVRO_SCHEMA
    )
    result = await handler.process(avro_data)
    assert result["id"] == "test1"
    assert result["value"] == 42
    assert result["key"] == "value"

@pytest.mark.asyncio
async def test_avro_handler_invalid(handler_factory):
    handler = await handler_factory.create_handler(
        "avro",
        schema=AVRO_SCHEMA
    )
    with pytest.raises(ValueError):
        await handler.process(b"invalid avro data")

# Parquet Handler Tests
@pytest.mark.asyncio
async def test_parquet_handler(handler_factory):
    # Create test parquet file
    df = pd.DataFrame([
        {"id": "test1", "value": 42, "key": "value"},
        {"id": "test2", "value": 43, "key": "value2"}
    ])
    
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        df.to_parquet(f.name)
        temp_path = f.name
        
    try:
        handler = await handler_factory.create_handler("parquet")
        result = await handler.process(Path(temp_path))
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result.iloc[0]["id"] == "test1"
        assert result.iloc[0]["value"] == 42
    finally:
        os.unlink(temp_path)

# Integration Tests
@pytest.mark.asyncio
async def test_format_handler_metrics(handler_factory, handler_metrics):
    handler = await handler_factory.create_handler("json")
    
    # Process valid data
    await handler.process(SAMPLE_JSON)
    
    # Process invalid data
    try:
        await handler.process("invalid json")
    except ValueError:
        pass
    
    metrics = await handler_metrics.collector.get_metrics()
    
    # Verify metrics were recorded
    assert "JSONHandler_processing_time" in metrics
    assert "JSONHandler_success" in metrics
    assert "JSONHandler_errors" in metrics

@pytest.mark.asyncio
async def test_multiple_format_handling(handler_factory):
    # Test processing same data through different formats
    
    # JSON to YAML
    json_handler = await handler_factory.create_handler("json")
    json_result = await json_handler.process(SAMPLE_JSON)
    
    yaml_data = yaml.dump(json_result)
    yaml_handler = await handler_factory.create_handler("yaml")
    yaml_result = await yaml_handler.process(yaml_data)
    
    assert json_result == yaml_result
    
    # YAML to CSV (flattened)
    df = pd.DataFrame([yaml_result])
    csv_data = df.to_csv(index=False)
    
    csv_handler = await handler_factory.create_handler("csv")
    csv_result = await csv_handler.process(csv_data)
    
    assert csv_result[0]["id"] == yaml_result["id"] 