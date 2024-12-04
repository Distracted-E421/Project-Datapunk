import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.discovery import (
    ServiceSync,
    SyncConfig,
    SyncState,
    SyncError,
    ServiceRecord
)

@pytest.fixture
def sync_config():
    return SyncConfig(
        sync_interval=5,
        max_retries=3,
        retry_delay=0.1,
        batch_size=100,
        conflict_resolution="latest"
    )

@pytest.fixture
def service_sync(sync_config):
    return ServiceSync(config=sync_config)

@pytest.fixture
def sample_records():
    return [
        ServiceRecord(
            id=f"service-{i}",
            name="test-service",
            version=f"1.{i}.0",
            timestamp=datetime.utcnow(),
            metadata={"region": "us-west"}
        )
        for i in range(3)
    ]

@pytest.mark.asyncio
async def test_sync_initialization(service_sync, sync_config):
    assert service_sync.config == sync_config
    assert service_sync.state == SyncState.INITIALIZED
    assert not service_sync.is_syncing

@pytest.mark.asyncio
async def test_peer_discovery(service_sync):
    with patch('datapunk_shared.mesh.discovery.ServiceRegistry') as mock_registry:
        mock_registry.return_value.query.return_value = [
            ServiceRecord(
                id="peer-1",
                name="sync-peer",
                host="peer1.local",
                port=8080
            ),
            ServiceRecord(
                id="peer-2",
                name="sync-peer",
                host="peer2.local",
                port=8080
            )
        ]
        
        peers = await service_sync.discover_peers()
        
        assert len(peers) == 2
        assert all(p.name == "sync-peer" for p in peers)

@pytest.mark.asyncio
async def test_state_synchronization(service_sync, sample_records):
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "records": [r.__dict__ for r in sample_records]
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Sync with peer
        synced_records = await service_sync.sync_with_peer(
            peer_host="peer1.local",
            peer_port=8080
        )
        
        assert len(synced_records) == len(sample_records)
        assert all(isinstance(r, ServiceRecord) for r in synced_records)

@pytest.mark.asyncio
async def test_conflict_resolution(service_sync):
    # Create conflicting records
    base_time = datetime.utcnow()
    record1 = ServiceRecord(
        id="service-1",
        name="test-service",
        version="1.0.0",
        timestamp=base_time
    )
    record2 = ServiceRecord(
        id="service-1",
        name="test-service",
        version="1.1.0",
        timestamp=base_time + timedelta(seconds=1)
    )
    
    # Resolve conflict (latest wins)
    resolved = await service_sync.resolve_conflict(record1, record2)
    assert resolved.version == "1.1.0"

@pytest.mark.asyncio
async def test_batch_synchronization(service_sync, sample_records):
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_responses = [
            AsyncMock(
                json=AsyncMock(return_value={"records": [r.__dict__ for r in batch]})
            )
            for batch in [sample_records[:2], sample_records[2:]]
        ]
        mock_post.return_value.__aenter__.side_effect = mock_responses
        
        # Sync in batches
        all_records = await service_sync.sync_batch(
            peer_host="peer1.local",
            peer_port=8080,
            batch_size=2
        )
        
        assert len(all_records) == len(sample_records)

@pytest.mark.asyncio
async def test_sync_retry(service_sync):
    with patch('aiohttp.ClientSession.post') as mock_post:
        # Mock failure then success
        mock_post.return_value.__aenter__.side_effect = [
            Exception("Connection failed"),
            Exception("Connection failed"),
            AsyncMock(
                json=AsyncMock(return_value={"records": []})
            )
        ]
        
        await service_sync.sync_with_peer(
            peer_host="peer1.local",
            peer_port=8080
        )
        
        assert mock_post.call_count == 3

@pytest.mark.asyncio
async def test_sync_state_management(service_sync):
    state_changes = []
    
    def state_handler(old_state, new_state):
        state_changes.append((old_state, new_state))
    
    service_sync.on_state_change(state_handler)
    
    await service_sync.start_sync()
    await service_sync.pause_sync()
    await service_sync.resume_sync()
    await service_sync.stop_sync()
    
    assert len(state_changes) == 4
    assert state_changes[-1][1] == SyncState.STOPPED

@pytest.mark.asyncio
async def test_differential_sync(service_sync, sample_records):
    with patch('aiohttp.ClientSession.post') as mock_post:
        # Mock peer's last sync timestamp
        last_sync = datetime.utcnow() - timedelta(minutes=5)
        
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "records": [
                r.__dict__ for r in sample_records
                if r.timestamp > last_sync
            ]
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        changes = await service_sync.sync_changes(
            peer_host="peer1.local",
            peer_port=8080,
            since=last_sync
        )
        
        assert len(changes) <= len(sample_records)

@pytest.mark.asyncio
async def test_sync_validation(service_sync, sample_records):
    validation_results = []
    
    def validation_handler(record, is_valid):
        validation_results.append((record, is_valid))
    
    service_sync.on_validation(validation_handler)
    
    # Validate records
    await service_sync.validate_records(sample_records)
    
    assert len(validation_results) == len(sample_records)
    assert all(r[1] for r in validation_results)

@pytest.mark.asyncio
async def test_sync_metrics(service_sync, sample_records):
    with patch('datapunk_shared.metrics.MetricsCollector') as mock_collector:
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.json.return_value = {
                "records": [r.__dict__ for r in sample_records]
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            await service_sync.sync_with_peer(
                peer_host="peer1.local",
                peer_port=8080
            )
            
            mock_collector.return_value.record_counter.assert_called()
            mock_collector.return_value.record_histogram.assert_called()

@pytest.mark.asyncio
async def test_concurrent_sync(service_sync):
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"records": []}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Attempt concurrent syncs
        peers = [
            ("peer1.local", 8080),
            ("peer2.local", 8080),
            ("peer3.local", 8080)
        ]
        
        tasks = [
            service_sync.sync_with_peer(host, port)
            for host, port in peers
        ]
        
        await asyncio.gather(*tasks)
        assert mock_post.call_count == len(peers)

@pytest.mark.asyncio
async def test_sync_error_handling(service_sync):
    with patch('aiohttp.ClientSession.post') as mock_post:
        # Simulate various errors
        mock_post.return_value.__aenter__.side_effect = [
            Exception("Network error"),
            AsyncMock(
                json=AsyncMock(side_effect=ValueError("Invalid JSON"))
            ),
            AsyncMock(
                json=AsyncMock(return_value={"invalid": "response"})
            )
        ]
        
        for _ in range(3):
            with pytest.raises((SyncError, ValueError)):
                await service_sync.sync_with_peer(
                    peer_host="peer1.local",
                    peer_port=8080
                )

@pytest.mark.asyncio
async def test_sync_persistence(service_sync, sample_records):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Save sync state
        await service_sync.save_state()
        mock_file.write.assert_called_once()
        
        # Load sync state
        await service_sync.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_sync_filtering(service_sync, sample_records):
    # Add regions to records
    for i, record in enumerate(sample_records):
        record.metadata["region"] = "us-west" if i % 2 == 0 else "us-east"
    
    # Filter records by region
    filtered = await service_sync.filter_records(
        records=sample_records,
        filter_func=lambda r: r.metadata["region"] == "us-west"
    )
    
    assert len(filtered) == len(sample_records) // 2
    assert all(r.metadata["region"] == "us-west" for r in filtered)

@pytest.mark.asyncio
async def test_cleanup(service_sync):
    cleanup_called = False
    
    async def cleanup_handler():
        nonlocal cleanup_called
        cleanup_called = True
    
    service_sync.on_cleanup(cleanup_handler)
    
    await service_sync.cleanup()
    
    assert cleanup_called
    assert service_sync.state == SyncState.STOPPED 