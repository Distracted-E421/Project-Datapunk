# Core encryption module for Datapunk configuration management
# Implements PBKDF2-based Fernet encryption for secure config storage
# 
# Security Notes:
# - Uses PBKDF2-HMAC-SHA256 for key derivation with 100k iterations
# - Automatically handles salt generation and persistence
# - Designed for encrypting sensitive configuration values while maintaining structure

from typing import Dict, Any, Union
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import os
import structlog

logger = structlog.get_logger(__name__)

class ConfigEncryption:
    """
    Handles secure configuration encryption and decryption
    
    This class provides a consistent way to encrypt sensitive configuration values
    while preserving the structure of nested configuration dictionaries. It automatically
    detects sensitive keys and handles key derivation and salt management.
    
    Security Features:
    - PBKDF2 key derivation with SHA256
    - Automatic salt generation and management
    - Fernet symmetric encryption
    """
    
    def __init__(self, encryption_key: str, salt: bytes = None):
        # Allow external salt for loading existing configs, generate new one if not provided
        self.salt = salt or os.urandom(16)
        self.fernet = self._create_fernet(encryption_key)
    
    def _create_fernet(self, key: str) -> Fernet:
        """
        Creates a Fernet instance with a derived key using PBKDF2
        
        Uses PBKDF2-HMAC-SHA256 with 100k iterations for key derivation,
        providing strong protection against brute force attacks
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,  # High iteration count for security
        )
        key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return Fernet(key)
    
    def encrypt_value(self, value: str) -> str:
        """
        Encrypts a single value using Fernet symmetric encryption
        
        Handles encoding/decoding to ensure consistent string output
        Logs encryption failures for debugging
        """
        try:
            return self.fernet.encrypt(value.encode()).decode()
        except Exception as e:
            logger.error("Encryption failed", error=str(e))
            raise
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """
        Decrypts a single Fernet-encrypted value
        
        Handles encoding/decoding to ensure consistent string output
        Logs decryption failures which could indicate tampering
        """
        try:
            return self.fernet.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise
    
    def encrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively encrypts sensitive values in a configuration dictionary
        
        Preserves the structure of nested dictionaries while only encrypting
        values associated with sensitive keys (passwords, tokens, etc.)
        """
        
        def encrypt_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            result = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    result[key] = encrypt_dict(value)
                elif self._is_sensitive_key(key):
                    result[key] = self.encrypt_value(str(value))
                else:
                    result[key] = value
            return result
        
        return encrypt_dict(config)
    
    def decrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively decrypts sensitive values in a configuration dictionary
        
        Mirrors encrypt_config's behavior, maintaining dictionary structure
        while decrypting only the sensitive values
        """
        
        def decrypt_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            result = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    result[key] = decrypt_dict(value)
                elif self._is_sensitive_key(key):
                    result[key] = self.decrypt_value(str(value))
                else:
                    result[key] = value
            return result
        
        return decrypt_dict(config)
    
    def _is_sensitive_key(self, key: str) -> bool:
        """
        Determines if a configuration key contains sensitive information
        
        Uses a predefined list of patterns to identify keys that likely
        contain sensitive data requiring encryption
        
        TODO: Consider making patterns configurable or environment-specific
        """
        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential',
            'private', 'cert', 'salt', 'hash'
        ]
        return any(pattern in key.lower() for pattern in sensitive_patterns)
    
    def save_encrypted(self, config: Dict[str, Any], filepath: str) -> None:
        """
        Saves an encrypted configuration to a JSON file
        
        Stores both the encrypted config and the salt used for key derivation
        to allow later decryption. Salt is stored as base64 for JSON compatibility.
        """
        try:
            encrypted = self.encrypt_config(config)
            with open(filepath, 'w') as f:
                json.dump({
                    'salt': base64.b64encode(self.salt).decode(),
                    'config': encrypted
                }, f, indent=2)
        except Exception as e:
            logger.error("Failed to save encrypted config", error=str(e))
            raise
    
    @classmethod
    def load_encrypted(cls, filepath: str, encryption_key: str) -> Dict[str, Any]:
        """
        Loads and decrypts a configuration from a JSON file
        
        Reconstructs the encryption context using the stored salt and provided key,
        then decrypts the configuration data
        
        NOTE: Requires the same encryption key used during save_encrypted
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            salt = base64.b64decode(data['salt'])
            encryptor = cls(encryption_key, salt)
            return encryptor.decrypt_config(data['config'])
            
        except Exception as e:
            logger.error("Failed to load encrypted config", error=str(e))
            raise 