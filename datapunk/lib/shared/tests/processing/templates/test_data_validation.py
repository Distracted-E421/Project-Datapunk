import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from datapunk_shared.processing.templates.data_validation import (
    DataValidationTemplate,
    ValidationConfig,
    ValidationRule,
    ValidationResult,
    ValidationError
)

@pytest.fixture
def validation_config():
    return ValidationConfig(
        name="test_validation",
        version="1.0.0",
        rules=[
            ValidationRule(
                name="numeric_range",
                field="value",
                type="range",
                config={"min": 0, "max": 100}
            ),
            ValidationRule(
                name="string_pattern",
                field="id",
                type="pattern",
                config={"pattern": "^[A-Z]{2}\\d{4}$"}
            ),
            ValidationRule(
                name="date_range",
                field="timestamp",
                type="date_range",
                config={
                    "start": "2023-01-01T00:00:00Z",
                    "end": "2023-12-31T23:59:59Z"
                }
            )
        ],
        error_handling={
            "strict_mode": True,
            "max_errors": 10
        }
    )

@pytest.fixture
async def validation_template(validation_config):
    template = DataValidationTemplate(validation_config)
    await template.initialize()
    return template

@pytest.mark.asyncio
async def test_template_initialization(validation_template, validation_config):
    """Test validation template initialization"""
    assert validation_template.config == validation_config
    assert validation_template.is_initialized
    assert len(validation_template.rules) == len(validation_config.rules)

@pytest.mark.asyncio
async def test_numeric_range_validation(validation_template):
    """Test numeric range validation"""
    # Valid value
    data = {"value": 50}
    result = await validation_template.validate_field("value", data)
    assert result.is_valid
    
    # Invalid values
    invalid_data = [
        {"value": -1},    # Below min
        {"value": 150},   # Above max
        {"value": "50"}   # Wrong type
    ]
    
    for data in invalid_data:
        result = await validation_template.validate_field("value", data)
        assert not result.is_valid

@pytest.mark.asyncio
async def test_string_pattern_validation(validation_template):
    """Test string pattern validation"""
    # Valid value
    data = {"id": "AB1234"}
    result = await validation_template.validate_field("id", data)
    assert result.is_valid
    
    # Invalid values
    invalid_data = [
        {"id": "12AB34"},     # Wrong format
        {"id": "ABC123"},     # Wrong length
        {"id": "ab1234"}      # Wrong case
    ]
    
    for data in invalid_data:
        result = await validation_template.validate_field("id", data)
        assert not result.is_valid

@pytest.mark.asyncio
async def test_date_range_validation(validation_template):
    """Test date range validation"""
    # Valid value
    data = {"timestamp": "2023-06-15T12:00:00Z"}
    result = await validation_template.validate_field("timestamp", data)
    assert result.is_valid
    
    # Invalid values
    invalid_data = [
        {"timestamp": "2022-12-31T23:59:59Z"},  # Before range
        {"timestamp": "2024-01-01T00:00:00Z"},  # After range
        {"timestamp": "invalid_date"}           # Invalid format
    ]
    
    for data in invalid_data:
        result = await validation_template.validate_field("timestamp", data)
        assert not result.is_valid

@pytest.mark.asyncio
async def test_complete_validation(validation_template):
    """Test complete record validation"""
    # Valid record
    valid_record = {
        "id": "AB1234",
        "value": 50,
        "timestamp": "2023-06-15T12:00:00Z"
    }
    
    result = await validation_template.validate(valid_record)
    assert result.is_valid
    assert not result.errors
    
    # Invalid record
    invalid_record = {
        "id": "invalid",
        "value": 150,
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    result = await validation_template.validate(invalid_record)
    assert not result.is_valid
    assert len(result.errors) == 3

@pytest.mark.asyncio
async def test_batch_validation(validation_template):
    """Test batch validation"""
    records = [
        {
            "id": "AB1234",
            "value": 50,
            "timestamp": "2023-06-15T12:00:00Z"
        },
        {
            "id": "CD5678",
            "value": 75,
            "timestamp": "2023-07-15T12:00:00Z"
        },
        {
            "id": "invalid",
            "value": 150,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ]
    
    results = await validation_template.validate_batch(records)
    
    assert len(results) == len(records)
    assert sum(1 for r in results if r.is_valid) == 2
    assert sum(1 for r in results if not r.is_valid) == 1

@pytest.mark.asyncio
async def test_custom_validation_rules(validation_template):
    """Test custom validation rules"""
    # Add custom rule
    custom_rule = ValidationRule(
        name="custom_check",
        field="status",
        type="custom",
        config={"valid_values": ["active", "inactive"]}
    )
    
    validation_template.add_rule(custom_rule)
    
    # Test valid value
    data = {"status": "active"}
    result = await validation_template.validate_field("status", data)
    assert result.is_valid
    
    # Test invalid value
    data = {"status": "pending"}
    result = await validation_template.validate_field("status", data)
    assert not result.is_valid

@pytest.mark.asyncio
async def test_error_handling(validation_template):
    """Test error handling"""
    # Test with invalid input
    with pytest.raises(ValidationError):
        await validation_template.validate(None)
    
    # Test with missing field
    data = {"id": "AB1234"}  # Missing required fields
    result = await validation_template.validate(data)
    assert not result.is_valid
    assert len(result.errors) > 0

@pytest.mark.asyncio
async def test_validation_hooks(validation_template):
    """Test validation hooks"""
    pre_validate = AsyncMock()
    post_validate = AsyncMock()
    
    validation_template.add_pre_validate_hook(pre_validate)
    validation_template.add_post_validate_hook(post_validate)
    
    data = {"id": "AB1234", "value": 50}
    await validation_template.validate(data)
    
    pre_validate.assert_called_once()
    post_validate.assert_called_once()

@pytest.mark.asyncio
async def test_validation_metrics(validation_template):
    """Test validation metrics collection"""
    metrics = []
    validation_template.set_metrics_callback(metrics.append)
    
    # Validate some data
    data = {"id": "AB1234", "value": 50}
    await validation_template.validate(data)
    
    assert len(metrics) > 0
    assert any(m["type"] == "validation_duration" for m in metrics)
    assert any(m["type"] == "validation_result" for m in metrics)

@pytest.mark.asyncio
async def test_conditional_validation(validation_template):
    """Test conditional validation rules"""
    # Add conditional rule
    conditional_rule = ValidationRule(
        name="conditional_check",
        field="secondary_value",
        type="conditional",
        config={
            "condition_field": "value",
            "condition": "greater_than",
            "threshold": 50,
            "validation": {"min": 0, "max": 1000}
        }
    )
    
    validation_template.add_rule(conditional_rule)
    
    # Test when condition is met
    data = {
        "value": 75,
        "secondary_value": 500
    }
    result = await validation_template.validate(data)
    assert result.is_valid
    
    # Test when condition is not met
    data = {
        "value": 25,
        "secondary_value": 1500  # Would be invalid if checked
    }
    result = await validation_template.validate(data)
    assert result.is_valid  # Should pass because condition wasn't met