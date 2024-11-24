from typing import Optional, Dict, Any
import ssl
import jwt
import time
import logging
from dataclasses import dataclass
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from .auth_metrics import AuthMetrics

@dataclass
class ServiceCredentials:
    service_id: str
    api_key: str
    cert_path: Path
    key_path: Path
    ca_path: Path

class ServiceAuthenticator:
    def __init__(
        self,
        credentials_dir: Path,
        jwt_secret: str,
        metrics_enabled: bool = True
    ):
        self.credentials_dir = credentials_dir
        self.jwt_secret = jwt_secret
        self.logger = logging.getLogger(__name__)
        self.metrics = AuthMetrics() if metrics_enabled else None
        self._service_credentials: Dict[str, ServiceCredentials] = {}
        self._ssl_contexts: Dict[str, ssl.SSLContext] = {}

    async def register_service(self, credentials: ServiceCredentials) -> bool:
        """Register a service with its authentication credentials"""
        try:
            # Validate credentials
            if not all([
                credentials.cert_path.exists(),
                credentials.key_path.exists(),
                credentials.ca_path.exists()
            ]):
                raise ValueError("Certificate files not found")

            # Create SSL context for mTLS
            ssl_context = ssl.create_default_context(
                purpose=ssl.Purpose.SERVER_AUTH,
                cafile=str(credentials.ca_path)
            )
            ssl_context.load_cert_chain(
                certfile=str(credentials.cert_path),
                keyfile=str(credentials.key_path)
            )
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            ssl_context.check_hostname = True

            # Store credentials and SSL context
            self._service_credentials[credentials.service_id] = credentials
            self._ssl_contexts[credentials.service_id] = ssl_context

            if self.metrics:
                await self.metrics.record_service_registration(credentials.service_id)

            self.logger.info(f"Successfully registered service: {credentials.service_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register service {credentials.service_id}: {str(e)}")
            return False

    async def authenticate_request(
        self,
        service_id: str,
        api_key: str,
        request_data: Dict[str, Any]
    ) -> Optional[str]:
        """Authenticate a service request and return a JWT token"""
        try:
            credentials = self._service_credentials.get(service_id)
            if not credentials:
                self.logger.warning(f"Unknown service: {service_id}")
                return None

            if not self._verify_api_key(credentials.api_key, api_key):
                self.logger.warning(f"Invalid API key for service: {service_id}")
                return None

            # Generate JWT token
            token = self._generate_jwt(service_id, request_data)

            if self.metrics:
                await self.metrics.record_successful_auth(service_id)

            return token

        except Exception as e:
            self.logger.error(f"Authentication failed for {service_id}: {str(e)}")
            if self.metrics:
                await self.metrics.record_failed_auth(service_id)
            return None

    def get_ssl_context(self, service_id: str) -> Optional[ssl.SSLContext]:
        """Get SSL context for mTLS communication"""
        return self._ssl_contexts.get(service_id)

    def _verify_api_key(self, stored_key: str, provided_key: str) -> bool:
        """Verify API key using constant-time comparison"""
        from hmac import compare_digest
        return compare_digest(stored_key, provided_key)

    def _generate_jwt(self, service_id: str, request_data: Dict[str, Any]) -> str:
        """Generate JWT token for authenticated service"""
        payload = {
            'service_id': service_id,
            'request_data': request_data,
            'exp': int(time.time()) + 3600,  # 1 hour expiration
            'iat': int(time.time())
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

    async def verify_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            if self.metrics:
                await self.metrics.record_successful_token_verification(payload['service_id'])
            
            return payload

        except jwt.ExpiredSignatureError:
            self.logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Token verification failed: {str(e)}")
            return None 