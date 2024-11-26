"""
Cache Features Module - Provides data transformation capabilities for caching operations.

This module implements a flexible caching system with optional compression and encryption features.
It handles the transformation of data both before storing in cache and after retrieval,
ensuring data security and optimization of storage space.

Key components:
- CompressionHandler: Manages zlib-based data compression
- EncryptionHandler: Handles Fernet encryption with PBKDF2 key derivation
- CacheFeatureManager: Orchestrates the compression and encryption workflow
"""

from typing import Any, Optional
import zlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import logging

class CompressionHandler:
    """
    Handles data compression using zlib with configurable compression levels.
    
    The compression level (1-9) trades off compression speed vs compression ratio:
    - Lower levels (1-3): Faster compression, larger output size
    - Medium levels (4-6): Balanced performance (default: 6)
    - Higher levels (7-9): Better compression, slower performance
    """
    
    def __init__(self, compression_level: int = 6):
        self.compression_level = compression_level
        self.logger = logging.getLogger(__name__)

    def compress(self, data: str) -> bytes:
        """Compress string data"""
        try:
            return zlib.compress(data.encode(), self.compression_level)
        except Exception as e:
            self.logger.error(f"Compression failed: {str(e)}")
            return data.encode()

    def decompress(self, data: bytes) -> str:
        """Decompress bytes to string"""
        try:
            return zlib.decompress(data).decode()
        except Exception as e:
            self.logger.error(f"Decompression failed: {str(e)}")
            return data.decode()

class EncryptionHandler:
    """
    Provides secure data encryption using Fernet (symmetric encryption).
    
    Security features:
    - Uses PBKDF2 for key derivation with 100,000 iterations
    - SHA256 for hashing
    - Implements AES-128 in CBC mode with PKCS7 padding
    
    NOTE: The salt should be changed in production environments for enhanced security
    """
    
    def __init__(self, encryption_key: str, salt: bytes = b'datapunk_cache'):
        self.logger = logging.getLogger(__name__)
        self.fernet = self._setup_encryption(encryption_key, salt)

    def _setup_encryption(self, key: str, salt: bytes) -> Fernet:
        """
        Derives a secure encryption key using PBKDF2.
        
        SECURITY NOTE: The iteration count (100000) is chosen to balance
        security with performance. Adjust based on your security requirements.
        """
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
            return Fernet(key)
        except Exception as e:
            self.logger.error(f"Encryption setup failed: {str(e)}")
            raise

    def encrypt(self, data: str) -> bytes:
        """Encrypt string data"""
        try:
            return self.fernet.encrypt(data.encode())
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise

    def decrypt(self, data: bytes) -> str:
        """Decrypt bytes to string"""
        try:
            return self.fernet.decrypt(data).decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {str(e)}")
            raise

class CacheFeatureManager:
    """
    Orchestrates the data transformation pipeline for cache operations.
    
    The manager provides a flexible way to enable/disable compression and encryption,
    handling the proper order of operations:
    - For caching: JSON serialization → compression → encryption
    - For retrieval: decryption → decompression → JSON deserialization
    
    IMPORTANT: When encryption is enabled, an encryption key must be provided.
    """
    
    def __init__(
        self,
        compression_enabled: bool = False,
        encryption_enabled: bool = False,
        encryption_key: Optional[str] = None,
        compression_level: int = 6
    ):
        self.compression_enabled = compression_enabled
        self.encryption_enabled = encryption_enabled
        self.logger = logging.getLogger(__name__)

        if compression_enabled:
            self.compression = CompressionHandler(compression_level)
        if encryption_enabled:
            if not encryption_key:
                raise ValueError("Encryption key required when encryption is enabled")
            self.encryption = EncryptionHandler(encryption_key)

    async def process_for_cache(self, data: Any) -> bytes:
        """
        Prepares data for caching by applying the configured transformations.
        
        The transformation pipeline ensures that:
        1. All data is JSON-serializable
        2. Compression (if enabled) is applied before encryption
        3. Final output is always in bytes format
        
        IMPORTANT: Encryption should always be the last step to maintain security
        """
        try:
            # Convert to JSON string
            json_data = json.dumps(data)

            # Apply compression if enabled
            if self.compression_enabled:
                json_data = self.compression.compress(json_data)

            # Apply encryption if enabled
            if self.encryption_enabled:
                return self.encryption.encrypt(
                    json_data if isinstance(json_data, str) else json_data.decode()
                )

            return json_data.encode() if isinstance(json_data, str) else json_data

        except Exception as e:
            self.logger.error(f"Cache processing failed: {str(e)}")
            raise

    async def process_from_cache(self, data: bytes) -> Any:
        """
        Retrieves and transforms cached data back to its original format.
        
        The transformation pipeline reverses the caching process:
        1. Decryption (if enabled)
        2. Decompression (if enabled)
        3. JSON deserialization
        
        NOTE: Type checking is important here as data format can vary
        based on enabled features
        """
        try:
            # Decrypt if encryption is enabled
            if self.encryption_enabled:
                data = self.encryption.decrypt(data)

            # Decompress if compression is enabled
            if self.compression_enabled:
                data = self.compression.decompress(
                    data if isinstance(data, bytes) else data.encode()
                )

            # Parse JSON
            return json.loads(data if isinstance(data, str) else data.decode())

        except Exception as e:
            self.logger.error(f"Cache retrieval processing failed: {str(e)}")
            raise 