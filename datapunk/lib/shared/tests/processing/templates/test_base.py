import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datapunk_shared.processing.templates.base import (
    BaseTemplate,
    TemplateConfig,
    TemplateContext,
    TemplateError
)

@pytest.fixture
def template_config():
    return TemplateConfig(
        name="test_template",
        version="1.0.0",
        description="Test template",
        parameters={
            "param1": {"type": "string", "required": True},
            "param2": {"type": "number", "default": 42}
        }
    )

@pytest.fixture
def template_context():
    return TemplateContext(
        parameters={"param1": "test"},
        environment={"env_var": "test_env"},
        metadata={"meta_key": "meta_value"}
    )

@pytest.fixture
async def base_template(template_config):
    template = BaseTemplate(template_config)
    await template.initialize()
    return template

@pytest.mark.asyncio
async def test_template_initialization(base_template, template_config):
    """Test template initialization"""
    assert base_template.config == template_config
    assert base_template.is_initialized
    assert base_template.version == template_config.version

@pytest.mark.asyncio
async def test_parameter_validation(base_template, template_context):
    """Test parameter validation"""
    # Valid parameters
    result = await base_template.validate_parameters(template_context)
    assert result.is_valid
    assert not result.errors
    
    # Missing required parameter
    invalid_context = TemplateContext(
        parameters={},
        environment={},
        metadata={}
    )
    result = await base_template.validate_parameters(invalid_context)
    assert not result.is_valid
    assert "param1" in str(result.errors[0])
    
    # Invalid parameter type
    invalid_context = TemplateContext(
        parameters={"param1": "test", "param2": "not_a_number"},
        environment={},
        metadata={}
    )
    result = await base_template.validate_parameters(invalid_context)
    assert not result.is_valid
    assert "param2" in str(result.errors[0])

@pytest.mark.asyncio
async def test_default_parameters(base_template):
    """Test default parameter handling"""
    context = TemplateContext(
        parameters={"param1": "test"},  # Only provide required param
        environment={},
        metadata={}
    )
    
    processed = await base_template.process_parameters(context)
    assert processed.parameters["param2"] == 42  # Default value

@pytest.mark.asyncio
async def test_environment_variables(base_template, template_context):
    """Test environment variable handling"""
    result = await base_template.validate_environment(template_context)
    assert result.is_valid
    
    processed = await base_template.process_environment(template_context)
    assert processed.environment["env_var"] == "test_env"

@pytest.mark.asyncio
async def test_metadata_handling(base_template, template_context):
    """Test metadata handling"""
    result = await base_template.validate_metadata(template_context)
    assert result.is_valid
    
    processed = await base_template.process_metadata(template_context)
    assert processed.metadata["meta_key"] == "meta_value"

@pytest.mark.asyncio
async def test_template_hooks(base_template, template_context):
    """Test template processing hooks"""
    pre_process = AsyncMock()
    post_process = AsyncMock()
    
    base_template.add_pre_process_hook(pre_process)
    base_template.add_post_process_hook(post_process)
    
    await base_template.process(template_context)
    
    pre_process.assert_called_once()
    post_process.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(base_template):
    """Test error handling"""
    # Test with invalid context type
    with pytest.raises(TemplateError):
        await base_template.process(None)
    
    # Test with invalid parameters
    invalid_context = TemplateContext(
        parameters={},  # Missing required parameter
        environment={},
        metadata={}
    )
    with pytest.raises(TemplateError):
        await base_template.process(invalid_context)

@pytest.mark.asyncio
async def test_template_versioning(template_config):
    """Test template versioning"""
    # Create templates with different versions
    template1 = BaseTemplate(template_config)
    template2 = BaseTemplate(
        TemplateConfig(
            name="test_template",
            version="2.0.0",
            description="Updated template",
            parameters=template_config.parameters
        )
    )
    
    await template1.initialize()
    await template2.initialize()
    
    assert template1.version != template2.version
    assert template2.version == "2.0.0"

@pytest.mark.asyncio
async def test_template_inheritance(template_config):
    """Test template inheritance"""
    class CustomTemplate(BaseTemplate):
        async def custom_process(self, context):
            return "custom result"
    
    template = CustomTemplate(template_config)
    await template.initialize()
    
    assert isinstance(template, BaseTemplate)
    assert await template.custom_process(None) == "custom result"

@pytest.mark.asyncio
async def test_template_context_manipulation(base_template, template_context):
    """Test template context manipulation"""
    # Add dynamic parameter
    base_template.add_parameter(
        "dynamic_param",
        {"type": "string", "required": False}
    )
    
    # Update context
    updated_context = template_context.copy()
    updated_context.parameters["dynamic_param"] = "dynamic_value"
    
    result = await base_template.validate_parameters(updated_context)
    assert result.is_valid
    assert "dynamic_param" in updated_context.parameters 