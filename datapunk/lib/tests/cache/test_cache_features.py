import pytest
from unittest.mock import Mock, patch
import json
import zlib
import base64
from cryptography.fernet import Fernet

from datapunk_shared.cache.cache_features import (
    CompressionHandler,
    EncryptionHandler,
    CacheFeatureManager
)

class TestCompressionHandler:
    @pytest.fixture
    def compression_handler(self):
        """Create compression handler with default level."""
        return CompressionHandler()

    @pytest.fixture
    def test_data(self):
        """Sample data for compression tests."""
        return "test" * 1000  # Create reasonably sized test data

    def test_compression_decompression(self, compression_handler, test_data):
        """Test complete compression and decompression cycle."""
        compressed = compression_handler.compress(test_data)
        decompressed = compression_handler.decompress(compressed)
        
        assert isinstance(compressed, bytes)
        assert len(compressed) < len(test_data)
        assert decompressed == test_data

    def test_compression_levels(self, test_data):
        """Test different compression levels."""
        # Test with lowest and highest compression levels
        low_compression = CompressionHandler(compression_level=1)
        high_compression = CompressionHandler(compression_level=9)
        
        low_result = low_compression.compress(test_data)
        high_result = high_compression.compress(test_data)
        
        # Higher compression level should result in smaller size
        assert len(high_result) <= len(low_result)

    def test_compression_failure_handling(self, compression_handler):
        """Test handling of compression failures."""
        with patch('zlib.compress', side_effect=Exception("Compression failed")):
            result = compression_handler.compress("test")
            assert result == b"test"

    def test_decompression_failure_handling(self, compression_handler):
        """Test handling of decompression failures."""
        with patch('zlib.decompress', side_effect=Exception("Decompression failed")):
            result = compression_handler.decompress(b"invalid_data")
            assert result == "invalid_data"

class TestEncryptionHandler:
    @pytest.fixture
    def encryption_key(self):
        """Sample encryption key for testing."""
        return "test_encryption_key_12345"

    @pytest.fixture
    def encryption_handler(self, encryption_key):
        """Create encryption handler."""
        return EncryptionHandler(encryption_key)

    @pytest.fixture
    def test_data(self):
        """Sample data for encryption tests."""
        return "sensitive_data_123"

    def test_encryption_decryption(self, encryption_handler, test_data):
        """Test complete encryption and decryption cycle."""
        encrypted = encryption_handler.encrypt(test_data)
        decrypted = encryption_handler.decrypt(encrypted)
        
        assert isinstance(encrypted, bytes)
        assert encrypted != test_data.encode()
        assert decrypted == test_data

    def test_encryption_with_different_keys(self, test_data):
        """Test that different keys produce different encrypted results."""
        handler1 = EncryptionHandler("key1")
        handler2 = EncryptionHandler("key2")
        
        encrypted1 = handler1.encrypt(test_data)
        encrypted2 = handler2.encrypt(test_data)
        
        assert encrypted1 != encrypted2

    def test_encryption_failure_handling(self, encryption_handler):
        """Test handling of encryption failures."""
        with patch.object(encryption_handler.fernet, 'encrypt',
                         side_effect=Exception("Encryption failed")):
            with pytest.raises(Exception):
                encryption_handler.encrypt("test")

    def test_decryption_failure_handling(self, encryption_handler):
        """Test handling of decryption failures."""
        with patch.object(encryption_handler.fernet, 'decrypt',
                         side_effect=Exception("Decryption failed")):
            with pytest.raises(Exception):
                encryption_handler.decrypt(b"invalid_data")

    def test_key_derivation(self, encryption_key):
        """Test key derivation process."""
        handler = EncryptionHandler(encryption_key)
        assert isinstance(handler.fernet, Fernet)

class TestCacheFeatureManager:
    @pytest.fixture
    def encryption_key(self):
        """Sample encryption key for testing."""
        return "test_encryption_key_12345"

    @pytest.fixture
    def test_data(self):
        """Sample data for feature tests."""
        return {
            "string": "test",
            "number": 123,
            "nested": {"key": "value"}
        }

    @pytest.mark.asyncio
    async def test_basic_manager(self, test_data):
        """Test manager with no features enabled."""
        manager = CacheFeatureManager()
        processed = await manager.process_for_cache(test_data)
        retrieved = await manager.process_from_cache(processed)
        
        assert isinstance(processed, bytes)
        assert retrieved == test_data

    @pytest.mark.asyncio
    async def test_compression_only(self, test_data):
        """Test manager with only compression enabled."""
        manager = CacheFeatureManager(compression_enabled=True)
        processed = await manager.process_for_cache(test_data)
        retrieved = await manager.process_from_cache(processed)
        
        assert isinstance(processed, bytes)
        assert len(processed) < len(json.dumps(test_data).encode())
        assert retrieved == test_data

    @pytest.mark.asyncio
    async def test_encryption_only(self, test_data, encryption_key):
        """Test manager with only encryption enabled."""
        manager = CacheFeatureManager(
            encryption_enabled=True,
            encryption_key=encryption_key
        )
        processed = await manager.process_for_cache(test_data)
        retrieved = await manager.process_from_cache(processed)
        
        assert isinstance(processed, bytes)
        assert processed != json.dumps(test_data).encode()
        assert retrieved == test_data

    @pytest.mark.asyncio
    async def test_compression_and_encryption(self, test_data, encryption_key):
        """Test manager with both compression and encryption enabled."""
        manager = CacheFeatureManager(
            compression_enabled=True,
            encryption_enabled=True,
            encryption_key=encryption_key
        )
        processed = await manager.process_for_cache(test_data)
        retrieved = await manager.process_from_cache(processed)
        
        assert isinstance(processed, bytes)
        assert processed != json.dumps(test_data).encode()
        assert retrieved == test_data

    def test_invalid_configuration(self):
        """Test manager creation with invalid configuration."""
        with pytest.raises(ValueError):
            CacheFeatureManager(encryption_enabled=True)  # Missing key

    @pytest.mark.asyncio
    async def test_process_for_cache_failure(self, test_data):
        """Test handling of processing failures."""
        manager = CacheFeatureManager(compression_enabled=True)
        with patch('json.dumps', side_effect=Exception("Processing failed")):
            with pytest.raises(Exception):
                await manager.process_for_cache(test_data)

    @pytest.mark.asyncio
    async def test_process_from_cache_failure(self, test_data):
        """Test handling of retrieval failures."""
        manager = CacheFeatureManager(compression_enabled=True)
        with patch('json.loads', side_effect=Exception("Retrieval failed")):
            with pytest.raises(Exception):
                await manager.process_from_cache(b"invalid_data") 