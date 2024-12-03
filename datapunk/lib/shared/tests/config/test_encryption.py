import pytest
from unittest.mock import Mock, patch
import json
import base64
import os
from cryptography.fernet import Fernet

from datapunk_shared.config.encryption import ConfigEncryption

@pytest.fixture
def encryption_key():
    """Sample encryption key for testing."""
    return "test_encryption_key_that_is_at_least_32_chars"

@pytest.fixture
def test_salt():
    """Fixed salt for testing."""
    return b'test_salt_12345'

@pytest.fixture
def config_encryption(encryption_key, test_salt):
    """Create config encryption instance with fixed salt."""
    return ConfigEncryption(encryption_key, test_salt)

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "database": {
            "host": "localhost",
            "port": 5432,
            "password": "secret123",
            "api_key": "abc123",
            "settings": {
                "timeout": 30,
                "private_key": "xyz789"
            }
        },
        "service": {
            "name": "test-service",
            "token": "test-token"
        }
    }

class TestConfigEncryption:
    def test_initialization(self, encryption_key):
        """Test encryption initialization."""
        # Test with provided salt
        encryptor = ConfigEncryption(encryption_key, b'test_salt')
        assert isinstance(encryptor.fernet, Fernet)
        assert encryptor.salt == b'test_salt'
        
        # Test with auto-generated salt
        encryptor = ConfigEncryption(encryption_key)
        assert isinstance(encryptor.fernet, Fernet)
        assert len(encryptor.salt) == 16  # Default salt length

    def test_value_encryption_decryption(self, config_encryption):
        """Test encryption and decryption of single values."""
        test_value = "test_secret_value"
        
        # Encrypt value
        encrypted = config_encryption.encrypt_value(test_value)
        assert encrypted != test_value
        assert isinstance(encrypted, str)
        
        # Decrypt value
        decrypted = config_encryption.decrypt_value(encrypted)
        assert decrypted == test_value

    def test_config_encryption_decryption(self, config_encryption, sample_config):
        """Test encryption and decryption of configuration dictionary."""
        # Encrypt config
        encrypted_config = config_encryption.encrypt_config(sample_config)
        
        # Verify sensitive values are encrypted
        assert encrypted_config["database"]["password"] != sample_config["database"]["password"]
        assert encrypted_config["database"]["api_key"] != sample_config["database"]["api_key"]
        assert encrypted_config["database"]["settings"]["private_key"] != sample_config["database"]["settings"]["private_key"]
        assert encrypted_config["service"]["token"] != sample_config["service"]["token"]
        
        # Verify non-sensitive values are unchanged
        assert encrypted_config["database"]["host"] == sample_config["database"]["host"]
        assert encrypted_config["database"]["port"] == sample_config["database"]["port"]
        assert encrypted_config["service"]["name"] == sample_config["service"]["name"]
        
        # Decrypt config
        decrypted_config = config_encryption.decrypt_config(encrypted_config)
        assert decrypted_config == sample_config

    def test_sensitive_key_detection(self, config_encryption):
        """Test detection of sensitive configuration keys."""
        sensitive_keys = [
            "password",
            "secret",
            "key",
            "token",
            "credential",
            "private",
            "cert",
            "salt",
            "hash"
        ]
        
        for key in sensitive_keys:
            assert config_encryption._is_sensitive_key(key) is True
            assert config_encryption._is_sensitive_key(key.upper()) is True
            assert config_encryption._is_sensitive_key(f"test_{key}") is True
            assert config_encryption._is_sensitive_key(f"{key}_test") is True

        non_sensitive_keys = [
            "username",
            "host",
            "port",
            "name",
            "setting",
            "config"
        ]
        
        for key in non_sensitive_keys:
            assert config_encryption._is_sensitive_key(key) is False

    def test_file_operations(self, config_encryption, sample_config, tmp_path):
        """Test saving and loading encrypted configuration files."""
        config_file = tmp_path / "test_config.json"
        
        # Save encrypted config
        config_encryption.save_encrypted(sample_config, str(config_file))
        
        # Verify file exists and contains expected structure
        assert config_file.exists()
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
            assert "salt" in saved_data
            assert "config" in saved_data
            assert base64.b64decode(saved_data["salt"]) == config_encryption.salt
        
        # Load and decrypt config
        loaded_config = ConfigEncryption.load_encrypted(
            str(config_file),
            config_encryption._encryption_key
        )
        assert loaded_config == sample_config

    def test_error_handling(self, config_encryption):
        """Test error handling in encryption operations."""
        # Test encryption failure
        with patch.object(config_encryption.fernet, 'encrypt',
                         side_effect=Exception("Encryption failed")):
            with pytest.raises(Exception):
                config_encryption.encrypt_value("test")
        
        # Test decryption failure
        with patch.object(config_encryption.fernet, 'decrypt',
                         side_effect=Exception("Decryption failed")):
            with pytest.raises(Exception):
                config_encryption.decrypt_value("invalid_data")
        
        # Test file operation failures
        with pytest.raises(Exception):
            ConfigEncryption.load_encrypted("nonexistent_file.json", "key")

    def test_different_keys(self, sample_config):
        """Test that different keys produce different encrypted results."""
        encryptor1 = ConfigEncryption("key1" + "x" * 28)  # Pad to 32 chars
        encryptor2 = ConfigEncryption("key2" + "x" * 28)  # Pad to 32 chars
        
        encrypted1 = encryptor1.encrypt_config(sample_config)
        encrypted2 = encryptor2.encrypt_config(sample_config)
        
        # Verify encrypted values are different
        assert encrypted1 != encrypted2
        
        # Verify each can only decrypt its own encryption
        decrypted1 = encryptor1.decrypt_config(encrypted1)
        with pytest.raises(Exception):
            encryptor2.decrypt_config(encrypted1)
        
        assert decrypted1 == sample_config 