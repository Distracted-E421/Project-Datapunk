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
    """Handles configuration encryption and decryption"""
    
    def __init__(self, encryption_key: str, salt: bytes = None):
        self.salt = salt or os.urandom(16)
        self.fernet = self._create_fernet(encryption_key)
    
    def _create_fernet(self, key: str) -> Fernet:
        """Create Fernet instance from key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return Fernet(key)
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a single value"""
        try:
            return self.fernet.encrypt(value.encode()).decode()
        except Exception as e:
            logger.error("Encryption failed", error=str(e))
            raise
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a single value"""
        try:
            return self.fernet.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise
    
    def encrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive configuration values"""
        encrypted = {}
        
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
        """Decrypt sensitive configuration values"""
        decrypted = {}
        
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
        """Check if key contains sensitive information"""
        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential',
            'private', 'cert', 'salt', 'hash'
        ]
        return any(pattern in key.lower() for pattern in sensitive_patterns)
    
    def save_encrypted(self, config: Dict[str, Any], filepath: str) -> None:
        """Save encrypted configuration to file"""
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
        """Load and decrypt configuration from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            salt = base64.b64decode(data['salt'])
            encryptor = cls(encryption_key, salt)
            return encryptor.decrypt_config(data['config'])
            
        except Exception as e:
            logger.error("Failed to load encrypted config", error=str(e))
            raise 