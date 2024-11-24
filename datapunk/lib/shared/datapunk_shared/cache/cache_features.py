from typing import Any, Optional
import zlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json
import logging

class CompressionHandler:
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
    def __init__(self, encryption_key: str, salt: bytes = b'datapunk_cache'):
        self.logger = logging.getLogger(__name__)
        self.fernet = self._setup_encryption(encryption_key, salt)

    def _setup_encryption(self, key: str, salt: bytes) -> Fernet:
        """Setup Fernet encryption with key derivation"""
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
        """Process data before caching"""
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
        """Process data after retrieving from cache"""
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