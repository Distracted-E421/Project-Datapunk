"""
Template Validator Tests
--------------------

Tests the template validation functionality including:
- Template structure validation
- Content validation
- Schema validation
- Error handling
- Performance monitoring

Run with: pytest -v test_template_validator.py
"""

import pytest
from datetime import datetime
from unittest.mock import Mock
import json

from datapunk_shared.auth.audit.reporting.template_validator import (
    TemplateValidator,
    ValidationResult,
    ValidationError
)
from datapunk_shared.auth.audit.reporting.templates import (
    TemplateType,
    TemplateContext,
    TemplateData
)

# Test Fixtures

@pytest.fixture
def validator():
    """Create template validator for testing."""
    return TemplateValidator()

@pytest.fixture
def valid_template():
    """Create valid template for testing."""
    return {
        "id": "test_template",
        "type": TemplateType.AUDIT.value,
        "version": "1.0",
        "name": "Test Template",
        "description": "Template for testing",
        "content": {
            "sections": ["summary", "details"],
            "fields": {
                "event_type": {"type": "string", "required": True},
                "timestamp": {"type": "datetime", "required": True},
                "user_id": {"type": "string", "required": False}
            },
            "formatting": {
                "date_format": "%Y-%m-%d %H:%M:%S",
                "timezone": "UTC"
            }
        }
    }

@pytest.fixture
def template_context():
    """Create template context for testing."""
    return TemplateContext(
        user_id="test_user",
        timestamp=datetime.utcnow(),
        correlation_id="test_correlation"
    )

# Structure Validation Tests

def test_valid_template_structure(validator, valid_template):
    """Test validation of valid template structure."""
    result = validator.validate_structure(valid_template)
    assert result.is_valid is True
    assert not result.errors

def test_missing_required_fields(validator):
    """Test validation of template with missing required fields."""
    invalid_template = {
        "id": "test_template",
        # Missing type
        "version": "1.0",
        "content": {}
    }
    
    result = validator.validate_structure(invalid_template)
    assert result.is_valid is False
    assert "type" in str(result.errors[0])

def test_invalid_field_types(validator):
    """Test validation of template with invalid field types."""
    invalid_template = {
        "id": "test_template",
        "type": TemplateType.AUDIT.value,
        "version": 1.0,  # Should be string
        "content": []  # Should be dict
    }
    
    result = validator.validate_structure(invalid_template)
    assert result.is_valid is False
    assert any("type" in str(err) for err in result.errors)

# Content Validation Tests

def test_valid_content(validator, valid_template):
    """Test validation of valid template content."""
    result = validator.validate_content(valid_template["content"])
    assert result.is_valid is True
    assert not result.errors

def test_invalid_sections(validator):
    """Test validation of template with invalid sections."""
    content = {
        "sections": "invalid",  # Should be list
        "fields": {}
    }
    
    result = validator.validate_content(content)
    assert result.is_valid is False
    assert "sections" in str(result.errors[0])

def test_invalid_field_definitions(validator):
    """Test validation of template with invalid field definitions."""
    content = {
        "sections": ["summary"],
        "fields": {
            "test": {"type": "invalid_type"},  # Invalid type
            "timestamp": {"type": "datetime", "format": 123}  # Invalid format
        }
    }
    
    result = validator.validate_content(content)
    assert result.is_valid is False
    assert len(result.errors) == 2

# Schema Validation Tests

def test_valid_schema(validator, valid_template):
    """Test validation against schema."""
    result = validator.validate_schema(valid_template)
    assert result.is_valid is True
    assert not result.errors

def test_schema_violations(validator):
    """Test validation of template violating schema."""
    invalid_template = {
        "id": "test_template",
        "type": "invalid_type",  # Invalid type
        "version": "1.0",
        "content": {
            "sections": ["summary"],
            "fields": {
                "test": {"required": "invalid"}  # Should be boolean
            }
        }
    }
    
    result = validator.validate_schema(invalid_template)
    assert result.is_valid is False
    assert len(result.errors) >= 2

def test_nested_schema_validation(validator):
    """Test validation of nested schema elements."""
    template = {
        "id": "test_template",
        "type": TemplateType.AUDIT.value,
        "version": "1.0",
        "content": {
            "sections": ["summary"],
            "fields": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "invalid_prop": {"type": 123}  # Invalid type definition
                    }
                }
            }
        }
    }
    
    result = validator.validate_schema(template)
    assert result.is_valid is False
    assert any("type" in str(err) for err in result.errors)

# Error Handling Tests

def test_validation_error_details(validator):
    """Test detailed error information in validation results."""
    invalid_template = {
        "id": "",  # Empty ID
        "type": "invalid",  # Invalid type
        "version": "invalid",  # Invalid version
        "content": None  # Invalid content
    }
    
    result = validator.validate(invalid_template)
    assert result.is_valid is False
    assert len(result.errors) >= 4
    
    # Verify error details
    error_messages = [str(err) for err in result.errors]
    assert any("id" in msg.lower() for msg in error_messages)
    assert any("type" in msg.lower() for msg in error_messages)
    assert any("version" in msg.lower() for msg in error_messages)
    assert any("content" in msg.lower() for msg in error_messages)

def test_validation_error_handling(validator):
    """Test handling of validation errors."""
    # None input
    with pytest.raises(ValidationError) as exc:
        validator.validate(None)
    assert "template" in str(exc.value).lower()
    
    # Invalid input type
    with pytest.raises(ValidationError) as exc:
        validator.validate(123)
    assert "dict" in str(exc.value).lower()

# Context Validation Tests

def test_template_context_validation(validator, valid_template, template_context):
    """Test validation with template context."""
    result = validator.validate_with_context(valid_template, template_context)
    assert result.is_valid is True
    assert not result.errors

def test_context_field_validation(validator, template_context):
    """Test validation of template fields against context."""
    template = {
        "id": "test_template",
        "type": TemplateType.AUDIT.value,
        "version": "1.0",
        "content": {
            "sections": ["summary"],
            "fields": {
                "user_id": {"type": "string", "required": True},
                "invalid_field": {"type": "string", "required": True}
            }
        }
    }
    
    result = validator.validate_with_context(template, template_context)
    assert result.is_valid is False
    assert "invalid_field" in str(result.errors[0])

# Performance Tests

def test_validation_performance(validator, valid_template):
    """Test validation performance with large templates."""
    # Create large template
    large_template = valid_template.copy()
    large_template["content"]["fields"].update({
        f"field_{i}": {
            "type": "string",
            "required": i % 2 == 0
        }
        for i in range(1000)
    })
    
    import time
    start_time = time.time()
    result = validator.validate(large_template)
    end_time = time.time()
    
    assert result.is_valid is True
    assert end_time - start_time < 1.0  # Should validate within 1 second

def test_bulk_validation(validator, valid_template):
    """Test bulk template validation performance."""
    templates = [valid_template.copy() for _ in range(100)]
    
    import time
    start_time = time.time()
    results = [validator.validate(t) for t in templates]
    end_time = time.time()
    
    assert all(r.is_valid for r in results)
    assert end_time - start_time < 2.0  # Should validate 100 templates within 2 seconds 