from typing import Optional, Dict, Any, Union, Tuple
from dataclasses import dataclass
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import serialization
import os
from ..monitoring import MetricsCollector

@dataclass
class EncryptionConfig:
    """Configuration for encryption"""
    key_size: int = 32  # bytes
    salt_size: int = 16  # bytes
    iterations: int = 100000
    algorithm: str = "AES-256-GCM"
    key_rotation_interval: int = 30 * 24 * 60 * 60  # 30 days in seconds
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    enable_key_derivation: bool = True
    enable_asymmetric: bool = True
    rsa_key_size: int = 2048
    padding_scheme: str = "PKCS7"

class EncryptionError(Exception):
    """Base class for encryption errors"""
    pass

class KeyDerivationError(EncryptionError):
    """Error during key derivation"""
    pass

class EncryptionKeyManager:
    """Manages encryption keys and rotation"""
    def __init__(self, config: EncryptionConfig):
        self.config = config
        self._current_key: Optional[bytes] = None
        self._previous_key: Optional[bytes] = None
        self._key_created_at: Optional[float] = None
        self._rsa_private_key: Optional[rsa.RSAPrivateKey] = None
        self._rsa_public_key: Optional[rsa.RSAPublicKey] = None

    def generate_key(self) -> bytes:
        """Generate a new encryption key"""
        return Fernet.generate_key()

    def derive_key(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Derive encryption key from password"""
        if not self.config.enable_key_derivation:
            raise KeyDerivationError("Key derivation is disabled")

        salt = salt or os.urandom(self.config.salt_size)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.config.key_size,
            salt=salt,
            iterations=self.config.iterations
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    def generate_rsa_keypair(self) -> Tuple[bytes, bytes]:
        """Generate RSA key pair"""
        if not self.config.enable_asymmetric:
            raise EncryptionError("Asymmetric encryption is disabled")

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.config.rsa_key_size
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem, public_pem

class DataEncryption:
    """Handles data encryption and decryption"""
    def __init__(
        self,
        config: EncryptionConfig,
        key_manager: EncryptionKeyManager,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.key_manager = key_manager
        self.metrics = metrics_collector
        self._fernet = None
        self._initialize_fernet()

    def _initialize_fernet(self):
        """Initialize Fernet cipher"""
        if not self.key_manager._current_key:
            self.key_manager._current_key = self.key_manager.generate_key()
        self._fernet = Fernet(self.key_manager._current_key)

    async def encrypt(
        self,
        data: Union[str, bytes, Dict],
        key: Optional[bytes] = None,
        compress: Optional[bool] = None
    ) -> bytes:
        """Encrypt data"""
        try:
            # Convert data to bytes
            if isinstance(data, dict):
                data = json.dumps(data).encode()
            elif isinstance(data, str):
                data = data.encode()

            # Compress if enabled and meets threshold
            should_compress = (
                (compress or self.config.enable_compression) and
                len(data) > self.config.compression_threshold
            )
            if should_compress:
                data = self._compress(data)

            # Encrypt data
            if key:
                # Use provided key
                fernet = Fernet(key)
                encrypted = fernet.encrypt(data)
            else:
                # Use current key
                encrypted = self._fernet.encrypt(data)

            if self.metrics:
                await self.metrics.increment(
                    "security.encryption.success",
                    tags={"compressed": str(should_compress)}
                )

            return encrypted

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "security.encryption.error",
                    tags={"error": str(e)}
                )
            raise EncryptionError(f"Encryption failed: {str(e)}")

    async def decrypt(
        self,
        data: bytes,
        key: Optional[bytes] = None,
        decompress: Optional[bool] = None
    ) -> Union[str, bytes, Dict]:
        """Decrypt data"""
        try:
            # Decrypt data
            if key:
                # Use provided key
                fernet = Fernet(key)
                decrypted = fernet.decrypt(data)
            else:
                # Try current key first, then previous key
                try:
                    decrypted = self._fernet.decrypt(data)
                except Exception:
                    if self.key_manager._previous_key:
                        previous_fernet = Fernet(self.key_manager._previous_key)
                        decrypted = previous_fernet.decrypt(data)
                    else:
                        raise

            # Decompress if needed
            if decompress or self.config.enable_compression:
                try:
                    decrypted = self._decompress(decrypted)
                except Exception:
                    # Data might not be compressed
                    pass

            # Try to parse as JSON
            try:
                return json.loads(decrypted)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return decrypted.decode()

            if self.metrics:
                await self.metrics.increment("security.decryption.success")

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "security.decryption.error",
                    tags={"error": str(e)}
                )
            raise EncryptionError(f"Decryption failed: {str(e)}")

    async def encrypt_asymmetric(
        self,
        data: bytes,
        public_key: bytes
    ) -> bytes:
        """Encrypt data using RSA public key"""
        if not self.config.enable_asymmetric:
            raise EncryptionError("Asymmetric encryption is disabled")

        try:
            key = serialization.load_pem_public_key(public_key)
            encrypted = key.encrypt(
                data,
                asym_padding.OAEP(
                    mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            if self.metrics:
                await self.metrics.increment("security.asymmetric_encryption.success")

            return encrypted

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "security.asymmetric_encryption.error",
                    tags={"error": str(e)}
                )
            raise EncryptionError(f"Asymmetric encryption failed: {str(e)}")

    async def decrypt_asymmetric(
        self,
        data: bytes,
        private_key: bytes
    ) -> bytes:
        """Decrypt data using RSA private key"""
        if not self.config.enable_asymmetric:
            raise EncryptionError("Asymmetric encryption is disabled")

        try:
            key = serialization.load_pem_private_key(
                private_key,
                password=None
            )
            decrypted = key.decrypt(
                data,
                asym_padding.OAEP(
                    mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            if self.metrics:
                await self.metrics.increment("security.asymmetric_decryption.success")

            return decrypted

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "security.asymmetric_decryption.error",
                    tags={"error": str(e)}
                )
            raise EncryptionError(f"Asymmetric decryption failed: {str(e)}")

    def _compress(self, data: bytes) -> bytes:
        """Compress data"""
        import zlib
        return zlib.compress(data)

    def _decompress(self, data: bytes) -> bytes:
        """Decompress data"""
        import zlib
        return zlib.decompress(data) 