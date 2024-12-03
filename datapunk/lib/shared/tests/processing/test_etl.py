import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.processing.etl import (
    ETLPipeline,
    ETLConfig,
    ETLStage,
    ETLResult,
    ETLError
)

@pytest.fixture
def etl_config():
    return ETLConfig(
        name="test_pipeline",
        stages=[
            ETLStage(
                name="extract",
                type="database",
                config={
                    "query": "SELECT * FROM test_table",
                    "batch_size": 1000
                }
            ),
            ETLStage(
                name="transform",
                type="data_transform",
                config={
                    "schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "value": {"type": "number"}
                        }
                    }
                }
            ),
            ETLStage(
                name="load",
                type="database",
                config={
                    "table": "processed_data",
                    "batch_size": 500
                }
            )
        ],
        error_handling={
            "max_retries": 3,
            "retry_delay": 5,
            "failure_threshold": 0.1  # 10% failure rate threshold
        }
    )

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
async def etl_pipeline(etl_config, mock_db):
    pipeline = ETLPipeline(etl_config)
    pipeline.db = mock_db
    await pipeline.initialize()
    return pipeline

@pytest.mark.asyncio
async def test_pipeline_initialization(etl_pipeline, etl_config):
    """Test ETL pipeline initialization"""
    assert etl_pipeline.config == etl_config
    assert etl_pipeline.is_initialized
    assert len(etl_pipeline.stages) == len(etl_config.stages)

@pytest.mark.asyncio
async def test_data_extraction(etl_pipeline, mock_db):
    """Test data extraction stage"""
    # Mock database response
    mock_db.fetch_all.return_value = [
        {"id": "1", "value": 100},
        {"id": "2", "value": 200}
    ]
    
    result = await etl_pipeline.execute_extract("extract")
    
    assert result.success
    assert len(result.data) == 2
    mock_db.fetch_all.assert_called_once()

@pytest.mark.asyncio
async def test_data_transformation(etl_pipeline):
    """Test data transformation stage"""
    input_data = [
        {"id": "1", "value": "100"},  # Value needs conversion
        {"id": "2", "value": "200"}
    ]
    
    result = await etl_pipeline.execute_transform("transform", input_data)
    
    assert result.success
    assert all(isinstance(item["value"], (int, float)) for item in result.data)

@pytest.mark.asyncio
async def test_data_loading(etl_pipeline, mock_db):
    """Test data loading stage"""
    processed_data = [
        {"id": "1", "value": 100},
        {"id": "2", "value": 200}
    ]
    
    result = await etl_pipeline.execute_load("load", processed_data)
    
    assert result.success
    mock_db.execute_batch.assert_called_once()

@pytest.mark.asyncio
async def test_pipeline_execution(etl_pipeline):
    """Test full pipeline execution"""
    # Mock successful execution of all stages
    with patch.object(etl_pipeline, 'execute_extract') as mock_extract, \
         patch.object(etl_pipeline, 'execute_transform') as mock_transform, \
         patch.object(etl_pipeline, 'execute_load') as mock_load:
        
        mock_extract.return_value = ETLResult(True, [{"id": "1", "value": "100"}])
        mock_transform.return_value = ETLResult(True, [{"id": "1", "value": 100}])
        mock_load.return_value = ETLResult(True, None)
        
        result = await etl_pipeline.execute()
        
        assert result.success
        mock_extract.assert_called_once()
        mock_transform.assert_called_once()
        mock_load.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(etl_pipeline):
    """Test error handling and retries"""
    # Mock extraction failure
    with patch.object(etl_pipeline, 'execute_extract') as mock_extract:
        mock_extract.side_effect = [
            ETLError("Database error"),  # First attempt fails
            ETLError("Database error"),  # Second attempt fails
            ETLResult(True, [{"id": "1", "value": "100"}])  # Third attempt succeeds
        ]
        
        result = await etl_pipeline.execute()
        
        assert result.success
        assert mock_extract.call_count == 3

@pytest.mark.asyncio
async def test_batch_processing(etl_pipeline, mock_db):
    """Test batch processing"""
    # Generate large dataset
    large_dataset = [
        {"id": str(i), "value": i * 100}
        for i in range(1000)
    ]
    mock_db.fetch_all.return_value = large_dataset
    
    result = await etl_pipeline.execute()
    
    assert result.success
    # Verify batch processing in load stage
    assert mock_db.execute_batch.call_count > 1

@pytest.mark.asyncio
async def test_data_validation(etl_pipeline):
    """Test data validation during transformation"""
    invalid_data = [
        {"id": "1", "value": "invalid"},  # Invalid value type
        {"id": "2", "value": 200}
    ]
    
    result = await etl_pipeline.execute_transform("transform", invalid_data)
    
    assert not result.success
    assert "validation" in str(result.error)

@pytest.mark.asyncio
async def test_pipeline_metrics(etl_pipeline):
    """Test pipeline metrics collection"""
    metrics = []
    etl_pipeline.set_metrics_callback(metrics.append)
    
    # Execute pipeline
    with patch.object(etl_pipeline, 'execute_extract') as mock_extract, \
         patch.object(etl_pipeline, 'execute_transform') as mock_transform, \
         patch.object(etl_pipeline, 'execute_load') as mock_load:
        
        mock_extract.return_value = ETLResult(True, [{"id": "1", "value": "100"}])
        mock_transform.return_value = ETLResult(True, [{"id": "1", "value": 100}])
        mock_load.return_value = ETLResult(True, None)
        
        await etl_pipeline.execute()
    
    assert len(metrics) > 0
    assert any(m["type"] == "pipeline_duration" for m in metrics)
    assert any(m["type"] == "records_processed" for m in metrics)

@pytest.mark.asyncio
async def test_pipeline_hooks(etl_pipeline):
    """Test pipeline execution hooks"""
    pre_execute = AsyncMock()
    post_execute = AsyncMock()
    
    etl_pipeline.add_pre_execute_hook(pre_execute)
    etl_pipeline.add_post_execute_hook(post_execute)
    
    # Execute pipeline with mocked stages
    with patch.object(etl_pipeline, 'execute_extract') as mock_extract, \
         patch.object(etl_pipeline, 'execute_transform') as mock_transform, \
         patch.object(etl_pipeline, 'execute_load') as mock_load:
        
        mock_extract.return_value = ETLResult(True, [])
        mock_transform.return_value = ETLResult(True, [])
        mock_load.return_value = ETLResult(True, None)
        
        await etl_pipeline.execute()
    
    pre_execute.assert_called_once()
    post_execute.assert_called_once()

@pytest.mark.asyncio
async def test_pipeline_state_tracking(etl_pipeline):
    """Test pipeline state tracking"""
    # Execute pipeline with mocked stages
    with patch.object(etl_pipeline, 'execute_extract') as mock_extract, \
         patch.object(etl_pipeline, 'execute_transform') as mock_transform, \
         patch.object(etl_pipeline, 'execute_load') as mock_load:
        
        mock_extract.return_value = ETLResult(True, [{"id": "1", "value": "100"}])
        mock_transform.return_value = ETLResult(True, [{"id": "1", "value": 100}])
        mock_load.return_value = ETLResult(True, None)
        
        await etl_pipeline.execute()
    
    state = etl_pipeline.get_pipeline_state()
    assert state.last_execution is not None
    assert state.success_count > 0
    assert state.error_count == 0 