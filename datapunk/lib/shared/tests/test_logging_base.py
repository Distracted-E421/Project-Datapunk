import pytest
import json
import structlog
from unittest.mock import MagicMock, patch
from datetime import datetime
from datapunk_shared.logging import TraceContextProcessor, configure_logging
from datapunk_shared.tracing import TracingManager

@pytest.fixture
def mock_tracing_manager():
    manager = MagicMock(spec=TracingManager)
    # Mock trace context injection
    manager.inject_context_to_log.side_effect = lambda event_dict: {
        **event_dict,
        'trace_id': 'test-trace-123',
        'span_id': 'test-span-456',
        'parent_span_id': 'test-parent-789',
        'sampled': True
    }
    return manager

@pytest.fixture
def trace_processor(mock_tracing_manager):
    return TraceContextProcessor(mock_tracing_manager)

def test_trace_context_processor_initialization(mock_tracing_manager):
    """Test trace context processor initialization"""
    processor = TraceContextProcessor(mock_tracing_manager)
    assert processor.tracing == mock_tracing_manager

def test_trace_context_processor_enrichment(trace_processor):
    """Test trace context enrichment of log events"""
    event_dict = {
        'event': 'test_event',
        'timestamp': '2023-01-01T00:00:00Z',
        'level': 'info'
    }
    
    result = trace_processor('test_logger', 'info', event_dict)
    
    assert result['trace_id'] == 'test-trace-123'
    assert result['span_id'] == 'test-span-456'
    assert result['parent_span_id'] == 'test-parent-789'
    assert result['sampled'] is True
    assert result['event'] == 'test_event'  # Original data preserved

def test_logging_configuration(mock_tracing_manager):
    """Test logging system configuration"""
    configure_logging('test-service', mock_tracing_manager)
    
    # Get configured logger
    logger = structlog.get_logger()
    
    # Verify logger configuration
    assert isinstance(logger, structlog.stdlib.BoundLogger)
    assert structlog.is_configured()

def test_log_event_formatting(mock_tracing_manager):
    """Test complete log event formatting pipeline"""
    configure_logging('test-service', mock_tracing_manager)
    logger = structlog.get_logger()
    
    # Capture log output
    with patch('structlog.processors.JSONRenderer.__call__') as json_renderer:
        json_renderer.side_effect = lambda _, __, event_dict: json.dumps(event_dict)
        
        # Generate test log event
        logger.info('test_message',
                   extra_field='test_value',
                   number=42)
        
        # Get the formatted log event
        call_args = json_renderer.call_args[0]
        event_dict = call_args[2]
        
        # Verify log event structure
        assert event_dict['event'] == 'test_message'
        assert event_dict['extra_field'] == 'test_value'
        assert event_dict['number'] == 42
        assert 'timestamp' in event_dict
        assert event_dict['level'] == 'info'
        assert event_dict['trace_id'] == 'test-trace-123'

def test_error_log_formatting(mock_tracing_manager):
    """Test error log formatting with stack traces"""
    configure_logging('test-service', mock_tracing_manager)
    logger = structlog.get_logger()
    
    # Capture log output
    with patch('structlog.processors.JSONRenderer.__call__') as json_renderer:
        json_renderer.side_effect = lambda _, __, event_dict: json.dumps(event_dict)
        
        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception('error_occurred')
        
        # Get the formatted log event
        call_args = json_renderer.call_args[0]
        event_dict = call_args[2]
        
        # Verify error log structure
        assert event_dict['event'] == 'error_occurred'
        assert event_dict['level'] == 'error'
        assert 'exception' in event_dict
        assert 'ValueError: Test error' in event_dict['exception']
        assert 'trace_id' in event_dict

def test_timestamp_formatting(mock_tracing_manager):
    """Test ISO timestamp formatting in log events"""
    configure_logging('test-service', mock_tracing_manager)
    logger = structlog.get_logger()
    
    with patch('structlog.processors.JSONRenderer.__call__') as json_renderer:
        json_renderer.side_effect = lambda _, __, event_dict: json.dumps(event_dict)
        
        logger.info('test_message')
        
        call_args = json_renderer.call_args[0]
        event_dict = call_args[2]
        
        # Verify timestamp format
        timestamp = event_dict['timestamp']
        # Should be able to parse as ISO format
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

def test_log_level_annotation(mock_tracing_manager):
    """Test log level annotation in events"""
    configure_logging('test-service', mock_tracing_manager)
    logger = structlog.get_logger()
    
    with patch('structlog.processors.JSONRenderer.__call__') as json_renderer:
        json_renderer.side_effect = lambda _, __, event_dict: json.dumps(event_dict)
        
        # Test different log levels
        logger.debug('debug_message')
        debug_event = json_renderer.call_args[0][2]
        assert debug_event['level'] == 'debug'
        
        logger.info('info_message')
        info_event = json_renderer.call_args[0][2]
        assert info_event['level'] == 'info'
        
        logger.warning('warning_message')
        warning_event = json_renderer.call_args[0][2]
        assert warning_event['level'] == 'warning'
        
        logger.error('error_message')
        error_event = json_renderer.call_args[0][2]
        assert error_event['level'] == 'error'

def test_context_preservation(mock_tracing_manager):
    """Test context preservation across log calls"""
    configure_logging('test-service', mock_tracing_manager)
    logger = structlog.get_logger()
    
    # Bind some context
    logger = logger.bind(request_id='test-req-123')
    
    with patch('structlog.processors.JSONRenderer.__call__') as json_renderer:
        json_renderer.side_effect = lambda _, __, event_dict: json.dumps(event_dict)
        
        # Generate multiple log events
        logger.info('first_event')
        first_event = json_renderer.call_args[0][2]
        
        logger.info('second_event')
        second_event = json_renderer.call_args[0][2]
        
        # Verify context is preserved
        assert first_event['request_id'] == 'test-req-123'
        assert second_event['request_id'] == 'test-req-123'

def test_nested_context_handling(mock_tracing_manager):
    """Test handling of nested context data"""
    configure_logging('test-service', mock_tracing_manager)
    logger = structlog.get_logger()
    
    nested_data = {
        'user': {
            'id': 123,
            'role': 'admin'
        },
        'metadata': {
            'version': '1.0',
            'environment': 'test'
        }
    }
    
    with patch('structlog.processors.JSONRenderer.__call__') as json_renderer:
        json_renderer.side_effect = lambda _, __, event_dict: json.dumps(event_dict)
        
        logger.info('test_event', **nested_data)
        
        event_dict = json_renderer.call_args[0][2]
        
        # Verify nested data structure
        assert event_dict['user']['id'] == 123
        assert event_dict['user']['role'] == 'admin'
        assert event_dict['metadata']['version'] == '1.0'
        assert event_dict['metadata']['environment'] == 'test' 