import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.processing.transformers import (
    DataTransformer,
    TransformConfig,
    TransformType,
    TransformResult,
    ValidationError
)

@pytest.fixture
def transform_config():
    return TransformConfig(
        name="test_transformer",
        transform_type=TransformType.STRUCTURED,
        schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "value": {"type": "number"},
                "timestamp": {"type": "string", "format": "date-time"}
            },
            "required": ["id", "value"]
        },
        validation_rules=[
            {"field": "value", "rule": "range", "min": 0, "max": 100},
            {"field": "id", "rule": "pattern", "pattern": "^[A-Z]{2}\\d{4}$"}
        ]
    )

@pytest.fixture
async def data_transformer(transform_config):
    transformer = DataTransformer(transform_config)
    await transformer.initialize()
    return transformer

@pytest.mark.asyncio
async def test_transformer_initialization(data_transformer, transform_config):
    """Test transformer initialization"""
    assert data_transformer.config == transform_config
    assert data_transformer.is_initialized
    assert len(data_transformer.validation_rules) == len(transform_config.validation_rules)

@pytest.mark.asyncio
async def test_schema_validation(data_transformer):
    """Test schema validation"""
    # Valid data
    valid_data = {
        "id": "AB1234",
        "value": 50,
        "timestamp": "2023-01-01T00:00:00Z"
    }
    result = await data_transformer.validate_schema(valid_data)
    assert result.is_valid
    assert not result.errors
    
    # Invalid data
    invalid_data = {
        "id": "invalid",
        "value": "not_a_number"
    }
    result = await data_transformer.validate_schema(invalid_data)
    assert not result.is_valid
    assert len(result.errors) > 0

@pytest.mark.asyncio
async def test_rule_validation(data_transformer):
    """Test rule validation"""
    # Valid data
    valid_data = {
        "id": "AB1234",
        "value": 50
    }
    result = await data_transformer.validate_rules(valid_data)
    assert result.is_valid
    assert not result.errors
    
    # Invalid value range
    invalid_data = {
        "id": "AB1234",
        "value": 150
    }
    result = await data_transformer.validate_rules(invalid_data)
    assert not result.is_valid
    assert "value" in str(result.errors[0])
    
    # Invalid ID pattern
    invalid_data = {
        "id": "invalid",
        "value": 50
    }
    result = await data_transformer.validate_rules(invalid_data)
    assert not result.is_valid
    assert "id" in str(result.errors[0])

@pytest.mark.asyncio
async def test_data_transformation(data_transformer):
    """Test data transformation"""
    input_data = {
        "id": "AB1234",
        "value": 50,
        "extra_field": "should_be_removed"
    }
    
    result = await data_transformer.transform(input_data)
    
    assert result.success
    assert "id" in result.data
    assert "value" in result.data
    assert "extra_field" not in result.data
    assert result.data["id"] == "AB1234"
    assert result.data["value"] == 50

@pytest.mark.asyncio
async def test_batch_transformation(data_transformer):
    """Test batch data transformation"""
    batch_data = [
        {"id": "AB1234", "value": 50},
        {"id": "CD5678", "value": 75},
        {"id": "invalid", "value": 150}  # Invalid data
    ]
    
    results = await data_transformer.transform_batch(batch_data)
    
    assert len(results) == len(batch_data)
    assert sum(1 for r in results if r.success) == 2
    assert sum(1 for r in results if not r.success) == 1

@pytest.mark.asyncio
async def test_custom_transformations(data_transformer):
    """Test custom transformation functions"""
    # Add custom transformation
    async def custom_transform(data):
        data["value"] = data["value"] * 2
        return data
    
    data_transformer.add_transform_function("double_value", custom_transform)
    
    input_data = {"id": "AB1234", "value": 25}
    result = await data_transformer.transform(input_data, ["double_value"])
    
    assert result.success
    assert result.data["value"] == 50

@pytest.mark.asyncio
async def test_error_handling(data_transformer):
    """Test error handling during transformation"""
    # Test with invalid input type
    with pytest.raises(ValidationError):
        await data_transformer.transform(None)
    
    # Test with missing required field
    invalid_data = {"value": 50}  # Missing id
    result = await data_transformer.transform(invalid_data)
    assert not result.success
    assert "required" in str(result.errors[0])

@pytest.mark.asyncio
async def test_transformation_hooks(data_transformer):
    """Test transformation hooks"""
    pre_transform = AsyncMock()
    post_transform = AsyncMock()
    
    data_transformer.add_pre_transform_hook(pre_transform)
    data_transformer.add_post_transform_hook(post_transform)
    
    input_data = {"id": "AB1234", "value": 50}
    await data_transformer.transform(input_data)
    
    pre_transform.assert_called_once()
    post_transform.assert_called_once()

@pytest.mark.asyncio
async def test_transformation_metrics(data_transformer):
    """Test transformation metrics collection"""
    metrics = []
    data_transformer.set_metrics_callback(metrics.append)
    
    # Transform some data
    input_data = {"id": "AB1234", "value": 50}
    await data_transformer.transform(input_data)
    
    assert len(metrics) > 0
    assert any(m["type"] == "transform_duration" for m in metrics)
    assert any(m["type"] == "validation_result" for m in metrics)

@pytest.mark.asyncio
async def test_complex_transformations(data_transformer):
    """Test complex transformation chains"""
    # Add multiple transformation steps
    async def step1(data):
        data["value"] = data["value"] * 2
        return data
    
    async def step2(data):
        data["value"] = data["value"] + 10
        return data
    
    data_transformer.add_transform_function("double", step1)
    data_transformer.add_transform_function("add_ten", step2)
    
    input_data = {"id": "AB1234", "value": 20}
    result = await data_transformer.transform(
        input_data,
        ["double", "add_ten"]
    )
    
    assert result.success
    assert result.data["value"] == 50  # (20 * 2) + 10