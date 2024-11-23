import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch
from src.mesh.mesh_integrator import MeshIntegrator
from src.config.storage_config import StorageConfig

@pytest.fixture
async def mesh_integrator():
    """Create a test instance of MeshIntegrator"""
    config = StorageConfig()
    integrator = MeshIntegrator(config)
    
    # Mock consul client
    mock_consul = Mock()
    mock_consul.agent.service.register = AsyncMock()
    mock_consul.catalog.service = AsyncMock()
    integrator.consul_client = mock_consul
    
    return integrator

@pytest.mark.asyncio
async def test_stream_data_handling(mesh_integrator):
    """Test handling of stream data"""
    # Mock service discovery
    mesh_integrator.discover_service = AsyncMock(return_value={
        'address': 'localhost',
        'port': 8000
    })
    
    # Test data
    test_data = {
        'type': 'stream_data',
        'payload': {
            'user_id': 'test123',
            'timestamp': datetime.utcnow().isoformat(),
            'data': {
                'source': 'google_takeout',
                'content_type': 'location_history',
                'records': [
                    {
                        'timestamp': '2024-03-20T10:00:00Z',
                        'latitude': 37.7749,
                        'longitude': -122.4194
                    }
                ]
            }
        }
    }
    
    # Mock HTTP response
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={'status': 'success', 'processed': 1}
        )
        
        result = await mesh_integrator.handle_stream_data(test_data)
        
        assert result['status'] == 'success'
        assert result['processed'] == 1

@pytest.mark.asyncio
async def test_nexus_request_handling(mesh_integrator):
    """Test handling of nexus requests"""
    # Mock service discovery
    mesh_integrator.discover_service = AsyncMock(return_value={
        'address': 'localhost',
        'port': 8001
    })
    
    # Test query
    test_query = {
        'type': 'nexus_request',
        'payload': {
            'query_type': 'vector_search',
            'vector': [0.1] * 1536,
            'limit': 10,
            'filters': {
                'content_type': 'location_history',
                'date_range': {
                    'start': '2024-03-01T00:00:00Z',
                    'end': '2024-03-20T23:59:59Z'
                }
            }
        }
    }
    
    # Mock HTTP response
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={
                'status': 'success',
                'results': [
                    {
                        'id': 'vec123',
                        'similarity': 0.95,
                        'metadata': {
                            'timestamp': '2024-03-20T10:00:00Z',
                            'source': 'google_takeout'
                        }
                    }
                ]
            }
        )
        
        result = await mesh_integrator.handle_nexus_request(test_query)
        
        assert result['status'] == 'success'
        assert len(result['results']) == 1
        assert result['results'][0]['similarity'] == 0.95

class AsyncMock(Mock):
    """Helper class for mocking async functions"""
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs) 