"""
Template Manager Tests
------------------

Tests the template management functionality including:
- Template loading and storage
- Template versioning
- Template rendering
- Context handling
- Performance optimization
- Error handling

Run with: pytest -v test_templates.py
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
import json

from datapunk_shared.auth.audit.reporting.templates import (
    TemplateManager,
    TemplateType,
    TemplateContext,
    TemplateData
)

# Test Fixtures

@pytest.fixture
def storage_client():
    """Mock storage client for testing."""
    client = AsyncMock()
    client.load = AsyncMock()
    client.store = AsyncMock()
    client.list = AsyncMock()
    return client

@pytest.fixture
def cache_client():
    """Mock cache client for testing."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    return client

@pytest.fixture
def metrics_client():
    """Mock metrics client for testing."""
    client = AsyncMock()
    client.increment = AsyncMock()
    client.timing = AsyncMock()
    return client

@pytest.fixture
def template_context():
    """Create template context for testing."""
    return TemplateContext(
        user_id="test_user",
        timestamp=datetime.utcnow(),
        correlation_id="test_correlation"
    )

@pytest.fixture
def template_manager(storage_client, cache_client, metrics_client):
    """Create template manager for testing."""
    return TemplateManager(
        storage=storage_client,
        cache=cache_client,
        metrics=metrics_client
    )

@pytest.fixture
def template_data():
    """Create template data for testing."""
    return TemplateData(
        id="test_template",
        type=TemplateType.AUDIT,
        version="1.0",
        name="Test Template",
        description="Template for testing",
        content={
            "sections": ["summary", "details"],
            "fields": {
                "event_type": {"type": "string", "required": True},
                "timestamp": {"type": "datetime", "required": True}
            },
            "formatting": {
                "date_format": "%Y-%m-%d %H:%M:%S",
                "timezone": "UTC"
            }
        }
    )

# Template Loading Tests

@pytest.mark.asyncio
async def test_template_loading(template_manager, template_data):
    """Test template loading."""
    # Mock storage response
    template_manager.storage.load.return_value = template_data.to_dict()
    
    template = await template_manager.load_template("test_template")
    
    assert template.id == template_data.id
    assert template.version == template_data.version
    assert template.type == template_data.type
    
    # Verify metrics
    template_manager.metrics.increment.assert_called_with(
        "templates_loaded",
        tags={"type": template_data.type.value}
    )

@pytest.mark.asyncio
async def test_template_caching(template_manager, template_data):
    """Test template caching behavior."""
    # First load - from storage
    template_manager.storage.load.return_value = template_data.to_dict()
    await template_manager.load_template("test_template")
    
    # Second load - from cache
    template_manager.cache.get.return_value = template_data.to_dict()
    await template_manager.load_template("test_template")
    
    # Verify cache usage
    template_manager.storage.load.assert_called_once()
    template_manager.cache.get.assert_called_with("test_template")

# Template Storage Tests

@pytest.mark.asyncio
async def test_template_storage(template_manager, template_data):
    """Test template storage."""
    await template_manager.store_template(template_data)
    
    template_manager.storage.store.assert_called_once()
    stored_data = template_manager.storage.store.call_args[0][0]
    assert stored_data["id"] == template_data.id
    assert stored_data["version"] == template_data.version

@pytest.mark.asyncio
async def test_template_versioning(template_manager, template_data):
    """Test template versioning."""
    # Store original version
    await template_manager.store_template(template_data)
    
    # Store new version
    new_template = template_data.copy()
    new_template.version = "2.0"
    await template_manager.store_template(new_template)
    
    # Load latest version
    template_manager.storage.load.return_value = new_template.to_dict()
    template = await template_manager.load_template(
        template_data.id,
        version="latest"
    )
    
    assert template.version == "2.0"

# Template Rendering Tests

@pytest.mark.asyncio
async def test_template_rendering(template_manager, template_data, template_context):
    """Test template rendering."""
    template_manager.storage.load.return_value = template_data.to_dict()
    
    data = {
        "event_type": "test_event",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = await template_manager.render_template(
        template_id=template_data.id,
        data=data,
        context=template_context
    )
    
    assert "summary" in result
    assert "details" in result
    assert data["event_type"] in str(result)

@pytest.mark.asyncio
async def test_template_formatting(template_manager, template_data):
    """Test template formatting options."""
    template_manager.storage.load.return_value = template_data.to_dict()
    
    timestamp = datetime.utcnow()
    data = {
        "event_type": "test_event",
        "timestamp": timestamp
    }
    
    result = await template_manager.render_template(
        template_id=template_data.id,
        data=data
    )
    
    # Verify date formatting
    expected_format = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    assert expected_format in str(result)

# Context Handling Tests

@pytest.mark.asyncio
async def test_context_injection(template_manager, template_data, template_context):
    """Test context injection in templates."""
    template_data.content["fields"]["user_id"] = {
        "type": "string",
        "required": True,
        "from_context": True
    }
    template_manager.storage.load.return_value = template_data.to_dict()
    
    data = {
        "event_type": "test_event",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = await template_manager.render_template(
        template_id=template_data.id,
        data=data,
        context=template_context
    )
    
    assert template_context.user_id in str(result)

@pytest.mark.asyncio
async def test_context_validation(template_manager, template_data):
    """Test context validation."""
    template_data.content["fields"]["user_id"] = {
        "type": "string",
        "required": True,
        "from_context": True
    }
    template_manager.storage.load.return_value = template_data.to_dict()
    
    # Missing required context
    with pytest.raises(ValueError) as exc:
        await template_manager.render_template(
            template_id=template_data.id,
            data={},
            context=TemplateContext()  # Empty context
        )
    assert "user_id" in str(exc.value)

# Performance Tests

@pytest.mark.asyncio
async def test_bulk_rendering(template_manager, template_data):
    """Test bulk template rendering performance."""
    template_manager.storage.load.return_value = template_data.to_dict()
    
    data_items = [
        {
            "event_type": f"event_{i}",
            "timestamp": datetime.utcnow().isoformat()
        }
        for i in range(100)
    ]
    
    results = await template_manager.render_many(
        template_id=template_data.id,
        data_items=data_items
    )
    
    assert len(results) == 100
    assert all("event_" in str(r) for r in results)
    
    # Verify performance metrics
    template_manager.metrics.timing.assert_called_with(
        "bulk_render_time",
        mock.ANY,
        tags={"count": 100}
    )

@pytest.mark.asyncio
async def test_template_precompilation(template_manager, template_data):
    """Test template precompilation."""
    template_manager.storage.load.return_value = template_data.to_dict()
    
    # Load and precompile
    await template_manager.precompile_template(template_data.id)
    
    # Render with precompiled template
    data = {
        "event_type": "test_event",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    result = await template_manager.render_template(
        template_id=template_data.id,
        data=data
    )
    
    assert result is not None
    template_manager.metrics.timing.assert_called_with(
        "render_time",
        mock.ANY,
        tags={"precompiled": True}
    )

# Error Handling Tests

@pytest.mark.asyncio
async def test_template_not_found(template_manager):
    """Test handling of missing templates."""
    template_manager.storage.load.return_value = None
    
    with pytest.raises(ValueError) as exc:
        await template_manager.load_template("nonexistent")
    assert "not found" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_invalid_template_data(template_manager, template_data):
    """Test handling of invalid template data."""
    # Invalid field type
    template_data.content["fields"]["invalid"] = {
        "type": "unknown_type"
    }
    template_manager.storage.load.return_value = template_data.to_dict()
    
    with pytest.raises(ValueError) as exc:
        await template_manager.load_template(template_data.id)
    assert "field type" in str(exc.value).lower()

@pytest.mark.asyncio
async def test_rendering_errors(template_manager, template_data):
    """Test handling of rendering errors."""
    template_manager.storage.load.return_value = template_data.to_dict()
    
    # Invalid data type
    data = {
        "event_type": 123,  # Should be string
        "timestamp": "invalid_date"  # Invalid date format
    }
    
    with pytest.raises(ValueError) as exc:
        await template_manager.render_template(
            template_id=template_data.id,
            data=data
        )
    assert "invalid" in str(exc.value).lower()

# Template Type Tests

@pytest.mark.asyncio
async def test_template_type_handling(template_manager):
    """Test handling of different template types."""
    templates = {
        TemplateType.AUDIT: {"audit_specific": True},
        TemplateType.SECURITY: {"security_specific": True},
        TemplateType.COMPLIANCE: {"compliance_specific": True}
    }
    
    for template_type, content in templates.items():
        template = TemplateData(
            id=f"{template_type.value}_template",
            type=template_type,
            version="1.0",
            content=content
        )
        
        await template_manager.store_template(template)
        template_manager.metrics.increment.assert_called_with(
            "templates_stored",
            tags={"type": template_type.value}
        ) 