from typing import Optional, Union, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key, load_pem_private_key
import os
import base64
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class EncryptionConfig:
    """Configuration for encryption operations"""
    key_rotation_days: int = 30
    min_key_size: int = 32
    salt_size: int = 16
    iterations: int = 100000
    symmetric_algorithm: str = "AES-256-GCM"
    
class EncryptionKey:
    """Manages encryption keys with rotation support"""
    def __init__(
        self,
        key: Optional[bytes] = None,
        created_at: Optional[datetime] = None,
        config: Optional[EncryptionConfig] = None
    ):
        self.config = config or EncryptionConfig()
        self.key = key or self._generate_key()
        self.created_at = created_at or datetime.utcnow()
        
    def needs_rotation(self) -> bool:
        age = datetime.utcnow() - self.created_at
        return age > timedelta(days=self.config.key_rotation_days)
        
    @staticmethod
    def _generate_key() -> bytes:
        return Fernet.generate_key()

class DataEncryption:
    """Handles symmetric encryption of data"""
    def __init__(self, key: EncryptionKey):
        self.key = key
        self.fernet = Fernet(self.key.key)
        
    def encrypt(self, data: Union[str, bytes, Dict]) -> bytes:
        """Encrypt data with automatic serialization"""
        if isinstance(data, dict):
            data = json.dumps(data).encode()
        elif isinstance(data, str):
            data = data.encode()
            
        try:
            return self.fernet.encrypt(data)
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")
            
    def decrypt(self, encrypted_data: bytes) -> Union[str, Dict]:
        """Decrypt data with automatic deserialization"""
        try:
            decrypted = self.fernet.decrypt(encrypted_data)
            
            # Try to parse as JSON first
            try:
                return json.loads(decrypted)
            except json.JSONDecodeError:
                return decrypted.decode()
                
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {str(e)}")

class StreamEncryption:
    """Handles streaming encryption for large data"""
    def __init__(self, key: EncryptionKey):
        self.key = key
        self.block_size = 16  # AES block size
        
    async def encrypt_stream(self, data_stream, chunk_size: int = 8192):
        """Encrypt a data stream"""
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(self.key.key),
            modes.GCM(iv)
        ).encryptor()
        
        # Yield IV first
        yield iv
        
        padder = padding.PKCS7(128).padder()
        
        try:
            async for chunk in data_stream:
                if not chunk:
                    break
                    
                padded_chunk = padder.update(chunk)
                encrypted_chunk = cipher.update(padded_chunk)
                
                if encrypted_chunk:
                    yield encrypted_chunk
                    
            # Handle final blocks
            final_padded = padder.finalize()
            final_encrypted = cipher.update(final_padded) + cipher.finalize()
            
            if final_encrypted:
                yield final_encrypted
                
            # Yield tag
            yield cipher.tag
            
        except Exception as e:
            raise EncryptionError(f"Stream encryption failed: {str(e)}")
            
    async def decrypt_stream(self, encrypted_stream, chunk_size: int = 8192):
        """Decrypt a data stream"""
        # Read IV first
        iv = await encrypted_stream.read(16)
        
        cipher = Cipher(
            algorithms.AES(self.key.key),
            modes.GCM(iv)
        ).decryptor()
        
        unpadder = padding.PKCS7(128).unpadder()
        
        try:
            async for chunk in encrypted_stream:
                if not chunk:
                    break
                    
                decrypted_chunk = cipher.update(chunk)
                unpadded_chunk = unpadder.update(decrypted_chunk)
                
                if unpadded_chunk:
                    yield unpadded_chunk
                    
            # Handle final blocks
            final_decrypted = cipher.finalize()
            final_unpadded = unpadder.finalize()
            
            if final_unpadded:
                yield final_unpadded
                
        except Exception as e:
            raise EncryptionError(f"Stream decryption failed: {str(e)}")

class KeyManager:
    """Manages encryption keys and rotation"""
    def __init__(self, config: Optional[EncryptionConfig] = None):
        self.config = config or EncryptionConfig()
        self.active_key = EncryptionKey(config=self.config)
        self.old_keys: Dict[datetime, EncryptionKey] = {}
        
    def rotate_key(self):
        """Rotate the active encryption key"""
        if self.active_key.needs_rotation():
            # Store old key
            self.old_keys[self.active_key.created_at] = self.active_key
            # Generate new key
            self.active_key = EncryptionKey(config=self.config)
            
            # Clean up old keys (keep last 2)
            if len(self.old_keys) > 2:
                oldest_date = min(self.old_keys.keys())
                del self.old_keys[oldest_date]
                
    def get_key_for_data(self, encrypted_data: bytes) -> EncryptionKey:
        """Find the correct key for decrypting data"""
        # Try active key first
        try:
            Fernet(self.active_key.key).decrypt(encrypted_data)
            return self.active_key
        except Exception:
            # Try old keys
            for key in self.old_keys.values():
                try:
                    Fernet(key.key).decrypt(encrypted_data)
                    return key
                except Exception:
                    continue
                    
            raise EncryptionError("No valid key found for decryption")

class EncryptionError(Exception):
    """Custom exception for encryption operations"""
    pass 