from typing import Optional, Dict, Any
import logging
from dataclasses import dataclass
from ..service_discovery import ServiceDiscovery, ServiceRegistration
from .service_auth import ServiceAuthenticator, ServiceCredentials
from .rate_limiter import RateLimiter, RateLimitConfig

@dataclass
class SecureServiceRegistration(ServiceRegistration):
    credentials: ServiceCredentials
    rate_limit: Optional[RateLimitConfig] = None

class AuthenticatedServiceDiscovery:
    def __init__(
        self,
        service_discovery: ServiceDiscovery,
        authenticator: ServiceAuthenticator,
        rate_limiter: RateLimiter
    ):
        self.service_discovery = service_discovery
        self.authenticator = authenticator
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger(__name__)

    async def register_secure_service(
        self,
        registration: SecureServiceRegistration
    ) -> bool:
        """Register a service with security configurations"""
        try:
            # First register authentication credentials
            auth_success = await self.authenticator.register_service(
                registration.credentials
            )
            if not auth_success:
                self.logger.error(
                    f"Failed to register authentication for service: {registration.name}"
                )
                return False

            # Configure rate limiting if specified
            if registration.rate_limit:
                await self.rate_limiter.configure_limit(
                    registration.credentials.service_id,
                    registration.rate_limit
                )

            # Register with service discovery
            discovery_success = await self.service_discovery.register_service(registration)
            if not discovery_success:
                self.logger.error(
                    f"Failed to register service discovery for: {registration.name}"
                )
                # Rollback auth registration
                await self.authenticator.deregister_service(
                    registration.credentials.service_id
                )
                return False

            return True

        except Exception as e:
            self.logger.error(
                f"Failed to register secure service {registration.name}: {str(e)}"
            )
            return False

    async def discover_secure_service(
        self,
        service_name: str,
        api_key: str,
        request_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Discover a service with authentication and rate limiting"""
        try:
            # Check rate limits first
            allowed, retry_after = await self.rate_limiter.check_rate_limit(service_name)
            if not allowed:
                self.logger.warning(
                    f"Rate limit exceeded for service {service_name}. "
                    f"Retry after: {retry_after}s"
                )
                return None

            # Authenticate the request
            token = await self.authenticator.authenticate_request(
                service_name,
                api_key,
                request_data
            )
            if not token:
                self.logger.warning(f"Authentication failed for service: {service_name}")
                return None

            # Discover service instance
            instance = await self.service_discovery.discover_service(service_name)
            if not instance:
                self.logger.warning(f"No instances found for service: {service_name}")
                return None

            # Get SSL context for mTLS
            ssl_context = self.authenticator.get_ssl_context(service_name)

            return {
                'instance': instance,
                'token': token,
                'ssl_context': ssl_context
            }

        except Exception as e:
            self.logger.error(
                f"Failed to discover secure service {service_name}: {str(e)}"
            )
            return None

    async def deregister_secure_service(self, service_name: str) -> bool:
        """Deregister a service and clean up security configurations"""
        try:
            # Deregister from service discovery
            discovery_success = await self.service_discovery.deregister_service(
                service_name
            )
            if not discovery_success:
                self.logger.error(
                    f"Failed to deregister service discovery for: {service_name}"
                )
                return False

            # Clean up authentication
            auth_success = await self.authenticator.deregister_service(service_name)
            if not auth_success:
                self.logger.warning(
                    f"Failed to deregister authentication for: {service_name}"
                )

            return True

        except Exception as e:
            self.logger.error(
                f"Failed to deregister secure service {service_name}: {str(e)}"
            )
            return False 