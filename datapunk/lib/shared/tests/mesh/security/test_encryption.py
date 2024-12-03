import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from cryptography.fernet import Fernet
from base64 import b64encode
from datetime import datetime, timedelta
from datapunk_shared.mesh.security import (
    EncryptionManager,
    EncryptionConfig,
    KeyInfo,
    EncryptionError
)

@pytest.fixture
def encryption_config():
    return EncryptionConfig(
        key_rotation_days=30,
        key_storage_path="/keys",
        encryption_algorithm="AES-256-GCM",
        enable_key_derivation=True
    )

@pytest.fixture
def encryption_manager(encryption_config):
    return EncryptionManager(config=encryption_config)

@pytest.fixture
def sample_key_info():
    return KeyInfo(
        key_id="key1",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        algorithm="AES-256-GCM",
        status="active"
    )

@pytest.mark.asyncio
async def test_encryption_initialization(encryption_manager, encryption_config):
    assert encryption_manager.config == encryption_config
    assert not encryption_manager.is_initialized
    assert encryption_manager.current_key is None

@pytest.mark.asyncio
async def test_key_generation():
    with patch('cryptography.fernet.Fernet.generate_key') as mock_generate:
        mock_generate.return_value = b"test_key"
        
        manager = EncryptionManager(EncryptionConfig(
            key_storage_path="/keys"
        ))
        
        key = await manager.generate_key()
        assert key is not None
        assert len(key) > 0
        mock_generate.assert_called_once()

@pytest.mark.asyncio
async def test_data_encryption_decryption(encryption_manager):
    test_data = b"sensitive data"
    
    # Initialize with a test key
    with patch.object(encryption_manager, '_load_or_generate_key') as mock_load:
        mock_load.return_value = Fernet.generate_key()
        await encryption_manager.initialize()
        
        # Encrypt data
        encrypted = await encryption_manager.encrypt(test_data)
        assert encrypted != test_data
        
        # Decrypt data
        decrypted = await encryption_manager.decrypt(encrypted)
        assert decrypted == test_data

@pytest.mark.asyncio
async def test_key_rotation(encryption_manager, sample_key_info):
    with patch.object(encryption_manager, '_store_key') as mock_store:
        with patch.object(encryption_manager, '_load_key_info') as mock_load:
            mock_load.return_value = sample_key_info
            
            old_key = encryption_manager.current_key
            await encryption_manager.rotate_keys()
            
            assert encryption_manager.current_key != old_key
            mock_store.assert_called_once()

@pytest.mark.asyncio
async def test_key_derivation():
    manager = EncryptionManager(EncryptionConfig(
        enable_key_derivation=True,
        key_storage_path="/keys"
    ))
    
    master_key = await manager.generate_key()
    derived_key1 = await manager.derive_key(master_key, b"context1")
    derived_key2 = await manager.derive_key(master_key, b"context2")
    
    assert derived_key1 != derived_key2
    assert len(derived_key1) == len(master_key)

@pytest.mark.asyncio
async def test_key_backup(encryption_manager):
    with patch('shutil.copy2') as mock_copy:
        await encryption_manager.backup_keys()
        mock_copy.assert_called()

@pytest.mark.asyncio
async def test_key_recovery(encryption_manager):
    with patch.object(encryption_manager, '_recover_key') as mock_recover:
        mock_recover.return_value = Fernet.generate_key()
        
        recovered = await encryption_manager.recover_key("backup.key")
        assert recovered is not None
        mock_recover.assert_called_once()

@pytest.mark.asyncio
async def test_key_validation(encryption_manager, sample_key_info):
    with patch.object(encryption_manager, '_validate_key') as mock_validate:
        mock_validate.return_value = True
        
        is_valid = await encryption_manager.validate_key(b"test_key")
        assert is_valid
        mock_validate.assert_called_once()

@pytest.mark.asyncio
async def test_encryption_with_context(encryption_manager):
    test_data = b"sensitive data"
    context = {"user_id": "123", "purpose": "test"}
    
    with patch.object(encryption_manager, '_load_or_generate_key') as mock_load:
        mock_load.return_value = Fernet.generate_key()
        await encryption_manager.initialize()
        
        encrypted = await encryption_manager.encrypt(test_data, context=context)
        decrypted = await encryption_manager.decrypt(encrypted, context=context)
        
        assert decrypted == test_data
        
        # Decryption with wrong context should fail
        wrong_context = {"user_id": "456", "purpose": "test"}
        with pytest.raises(EncryptionError):
            await encryption_manager.decrypt(encrypted, context=wrong_context)

@pytest.mark.asyncio
async def test_key_metrics_collection(encryption_manager, sample_key_info):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        with patch.object(encryption_manager, '_load_key_info') as mock_load:
            mock_load.return_value = sample_key_info
            
            await encryption_manager.collect_metrics()
            
            mock_collector.return_value.record_gauge.assert_called()

@pytest.mark.asyncio
async def test_key_expiration(encryption_manager):
    expired_key_info = KeyInfo(
        key_id="old_key",
        created_at=datetime.utcnow() - timedelta(days=31),
        expires_at=datetime.utcnow() - timedelta(days=1),
        algorithm="AES-256-GCM",
        status="expired"
    )
    
    with patch.object(encryption_manager, '_load_key_info') as mock_load:
        mock_load.return_value = expired_key_info
        
        with pytest.raises(EncryptionError):
            await encryption_manager.validate_key(b"test_key")

@pytest.mark.asyncio
async def test_key_events(encryption_manager):
    events = []
    
    def event_handler(event_type, key_info):
        events.append((event_type, key_info))
    
    encryption_manager.on_key_event(event_handler)
    
    with patch.object(encryption_manager, '_load_or_generate_key') as mock_load:
        mock_load.return_value = Fernet.generate_key()
        await encryption_manager.initialize()
        
        assert len(events) > 0
        assert events[0][0] == "key_generated"

@pytest.mark.asyncio
async def test_encryption_error_handling(encryption_manager):
    # Test with invalid key
    with pytest.raises(EncryptionError):
        await encryption_manager.encrypt(b"test", key=b"invalid_key")

@pytest.mark.asyncio
async def test_key_storage_security(encryption_manager):
    with patch('os.chmod') as mock_chmod:
        await encryption_manager.initialize()
        
        # Should set restrictive permissions on key storage
        mock_chmod.assert_called_with(encryption_manager.config.key_storage_path, 0o600)

@pytest.mark.asyncio
async def test_concurrent_encryption(encryption_manager):
    with patch.object(encryption_manager, '_load_or_generate_key') as mock_load:
        mock_load.return_value = Fernet.generate_key()
        await encryption_manager.initialize()
        
        test_data = [b"data1", b"data2", b"data3"]
        
        # Encrypt multiple items concurrently
        encrypted = await asyncio.gather(*[
            encryption_manager.encrypt(data)
            for data in test_data
        ])
        
        assert len(encrypted) == len(test_data)
        assert all(e != d for e, d in zip(encrypted, test_data)) 