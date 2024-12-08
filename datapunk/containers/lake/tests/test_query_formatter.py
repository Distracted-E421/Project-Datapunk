import pytest
from datetime import datetime
from ..src.query.formatter.formatter_core import (
    FormatStyle,
    FormatOptions,
    QueryFormatter,
    ResultFormatter,
    StreamingResultFormatter,
    ProgressFormatter
)

@pytest.fixture
def result_formatter():
    return ResultFormatter()

@pytest.fixture
def streaming_formatter():
    return StreamingResultFormatter(batch_size=2)

@pytest.fixture
def progress_formatter():
    return ProgressFormatter()

@pytest.fixture
def sample_data():
    return [
        {'id': 1, 'name': 'John', 'age': 30},
        {'id': 2, 'name': 'Jane', 'age': 25},
        {'id': 3, 'name': 'Bob', 'age': 35}
    ]

def test_text_table_formatting(result_formatter, sample_data):
    """Test text table formatting."""
    result = result_formatter.format_table(
        sample_data,
        headers=['id', 'name', 'age']
    )
    
    # Verify table structure
    lines = result.split('\n')
    assert len(lines) == 7  # 2 separators + header + 3 data rows + bottom separator
    assert all('|' in line for line in lines[1:-1])  # All content rows have pipes
    assert all('+' in line for line in [lines[0], lines[2], lines[-1]])  # Separators
    
    # Verify content
    assert 'John' in result
    assert '30' in result
    assert 'name' in result.lower()

def test_csv_formatting(result_formatter, sample_data):
    """Test CSV formatting."""
    result = result_formatter.format_table(
        sample_data,
        headers=['id', 'name', 'age'],
        format_type="csv"
    )
    
    lines = result.split('\n')
    assert len(lines) == 4  # Header + 3 data rows
    assert lines[0] == 'id,name,age'
    assert '1,John,30' in result
    assert '2,Jane,25' in result

def test_json_formatting(result_formatter, sample_data):
    """Test JSON formatting."""
    result = result_formatter.format_table(
        sample_data,
        format_type="json"
    )
    
    assert '"id": 1' in result
    assert '"name": "John"' in result
    assert '"age": 30' in result

def test_scalar_formatting(result_formatter):
    """Test scalar result formatting."""
    # Test text format
    assert result_formatter.format_scalar(42) == "42"
    assert result_formatter.format_scalar("test") == "test"
    
    # Test JSON format
    assert result_formatter.format_scalar(42, "json") == "42"
    assert result_formatter.format_scalar("test", "json") == '"test"'
    assert result_formatter.format_scalar({"key": "value"}, "json") == '{"key": "value"}'

def test_error_formatting(result_formatter):
    """Test error formatting."""
    error = ValueError("Test error")
    result = result_formatter.format_error(error)
    
    assert "Error" in result
    assert "Test error" in result

@pytest.mark.asyncio
async def test_streaming_formatter(streaming_formatter):
    """Test streaming result formatter."""
    # Start batch
    await streaming_formatter.start_batch(['id', 'name'])
    
    # Add rows
    result1 = await streaming_formatter.add_row({'id': 1, 'name': 'John'})
    assert not result1  # First row shouldn't trigger batch
    
    result2 = await streaming_formatter.add_row({'id': 2, 'name': 'Jane'})
    assert result2  # Second row should trigger batch
    assert 'John' in result2
    assert 'Jane' in result2
    
    # End batch
    result3 = await streaming_formatter.end_batch()
    assert not result3  # Buffer should be empty

def test_progress_formatting(progress_formatter):
    """Test progress formatting."""
    # Test simple progress
    result = progress_formatter.format_progress(50, 100)
    assert '[' in result
    assert ']' in result
    assert '50%' in result
    assert '50/100' in result
    
    # Test complete progress
    result = progress_formatter.format_progress(100, 100)
    assert '100%' in result
    assert '100/100' in result
    
    # Test zero progress
    result = progress_formatter.format_progress(0, 100)
    assert '0%' in result
    assert '0/100' in result

def test_stage_progress_formatting(progress_formatter):
    """Test multi-stage progress formatting."""
    stages = [
        {'name': 'Parse', 'current': 100, 'total': 100},
        {'name': 'Execute', 'current': 50, 'total': 100},
        {'name': 'Format', 'current': 0, 'total': 100}
    ]
    
    result = progress_formatter.format_stage_progress(stages)
    lines = result.split('\n')
    
    assert 'Overall Progress' in lines[0]
    assert '50%' in lines[0]  # (100 + 50 + 0) / 3
    assert 'Parse: [' in lines[1]
    assert 'Execute: [' in lines[2]
    assert 'Format: [' in lines[3]

def test_timing_formatting(progress_formatter):
    """Test execution timing formatting."""
    timing = {
        'Parse': 0.5,
        'Execute': 1.5,
        'Format': 0.2
    }
    
    result = progress_formatter.format_timing(timing)
    lines = result.split('\n')
    
    assert len(lines) == 4  # 3 stages + total
    assert 'Parse: 0.50s' in result
    assert 'Execute: 1.50s' in result
    assert 'Format: 0.20s' in result
    assert 'Total Time: 2.20s' in result

def test_empty_data_handling(result_formatter):
    """Test handling of empty data."""
    # Empty table
    assert result_formatter.format_table([]) == "No results"
    
    # Empty CSV
    assert result_formatter.format_table([], format_type="csv") == "No results"
    
    # Empty JSON
    assert result_formatter.format_table([], format_type="json") == "No results"

def test_invalid_format_type(result_formatter, sample_data):
    """Test handling of invalid format type."""
    result = result_formatter.format_table(
        sample_data,
        format_type="invalid"
    )
    assert "Unsupported format type" in result

def test_error_handling(result_formatter, progress_formatter):
    """Test error handling in formatters."""
    # Test invalid data in table formatter
    result = result_formatter.format_table(None)
    assert "Error" in result
    
    # Test invalid progress values
    result = progress_formatter.format_progress(100, 0)
    assert "Error" in result
    
    # Test invalid timing data
    result = progress_formatter.format_timing(None)
    assert "Error" in result

@pytest.mark.asyncio
async def test_streaming_error_handling(streaming_formatter):
    """Test error handling in streaming formatter."""
    # Test invalid row
    result = await streaming_formatter.add_row(None)
    assert "Error" in result
    
    # Test batch operations after error
    result = await streaming_formatter.end_batch()
    assert not result  # Should handle gracefully

def test_large_data_handling(result_formatter):
    """Test handling of large datasets."""
    # Create large dataset
    large_data = [
        {
            'id': i,
            'name': f"User{i}",
            'data': 'x' * 100  # Large field
        }
        for i in range(100)
    ]
    
    # Test different formats
    text_result = result_formatter.format_table(large_data)
    assert len(text_result.split('\n')) > 100
    
    csv_result = result_formatter.format_table(large_data, format_type="csv")
    assert len(csv_result.split('\n')) == 101  # Header + 100 rows
    
    json_result = result_formatter.format_table(large_data, format_type="json")
    assert len(json_result) > 1000  # Should be quite large

def test_unicode_handling(result_formatter):
    """Test handling of Unicode characters."""
    unicode_data = [
        {'id': 1, 'name': '测试', 'symbol': '🌟'},
        {'id': 2, 'name': 'тест', 'symbol': '🌍'}
    ]
    
    # Test different formats
    text_result = result_formatter.format_table(unicode_data)
    assert '测试' in text_result
    assert '🌟' in text_result
    
    csv_result = result_formatter.format_table(
        unicode_data,
        format_type="csv"
    )
    assert '测试' in csv_result
    assert '🌟' in csv_result
    
    json_result = result_formatter.format_table(
        unicode_data,
        format_type="json"
    )
    assert '测试' in json_result
    assert '🌟' in json_result 