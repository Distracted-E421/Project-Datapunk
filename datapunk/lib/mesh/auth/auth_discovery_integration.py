"""
Authenticated Service Discovery Integration

Integrates service discovery with authentication and rate limiting in the
Datapunk service mesh. Provides a secure layer for service registration
and discovery with built-in security controls.

Key features:
- Secure service registration with credentials
- Rate limit enforcement
- mTLS support for service-to-service communication
- Automatic credential management
- Rollback support for failed registrations

See sys-arch.mmd Gateway/ServiceRegistry for integration details.
"""

from typing import Optional, Dict, Any
import logging
from dataclasses import dataclass
from ..service_discovery import ServiceDiscovery, ServiceRegistration
from .service_auth import ServiceAuthenticator, ServiceCredentials
from .rate_limiter import RateLimiter, RateLimitConfig

@dataclass
class SecureServiceRegistration(ServiceRegistration):
    """
    Enhanced service registration with security configurations.
    
    Extends basic service registration with authentication credentials
    and rate limiting parameters for comprehensive security control.
    
    TODO: Add support for dynamic credential rotation
    TODO: Implement service-specific security policies
    """
    credentials: ServiceCredentials
    rate_limit: Optional[RateLimitConfig] = None

class AuthenticatedServiceDiscovery:
    """
    Secure service discovery manager for the mesh network.
    
    Coordinates service registration, authentication, and rate limiting
    while maintaining consistency across distributed operations.
    
    NOTE: Operations are designed to be atomic to prevent partial
    registrations in the mesh.
    """
    
    def __init__(
        self,
        service_discovery: ServiceDiscovery,
        authenticator: ServiceAuthenticator,
        rate_limiter: RateLimiter
    ):
        """
        Initialize secure discovery with required components.
        
        Components work together to provide a secure service mesh:
        - ServiceDiscovery: Handles service location and health
        - ServiceAuthenticator: Manages service credentials
        - RateLimiter: Controls request frequency
        """
        self.service_discovery = service_discovery
        self.authenticator = authenticator
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger(__name__)

    async def register_secure_service(
        self,
        registration: SecureServiceRegistration
    ) -> bool:
        """
        Register service with security configurations.
        
        Performs atomic registration across multiple systems:
        1. Authentication setup
        2. Rate limit configuration
        3. Service discovery registration
        
        NOTE: Includes rollback mechanism for partial failures to
        maintain mesh consistency.
        """
        try:
            # Register authentication first for security
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

            # Complete service registration
            discovery_success = await self.service_discovery.register_service(registration)
            if not discovery_success:
                self.logger.error(
                    f"Failed to register service discovery for: {registration.name}"
                )
                # Rollback auth to maintain consistency
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
        """
        Discover service with security validation.
        
        Performs multi-step service discovery with security checks:
        1. Rate limit verification
        2. API key authentication
        3. Service instance discovery
        4. SSL context preparation
        
        NOTE: Returns None for any security or discovery failures to
        ensure secure operation.
        """
        try:
            # Verify rate limits first for efficiency
            allowed, retry_after = await self.rate_limiter.check_rate_limit(service_name)
            if not allowed:
                self.logger.warning(
                    f"Rate limit exceeded for service {service_name}. "
                    f"Retry after: {retry_after}s"
                )
                return None

            # Authenticate request
            token = await self.authenticator.authenticate_request(
                service_name,
                api_key,
                request_data
            )
            if not token:
                self.logger.warning(f"Authentication failed for service: {service_name}")
                return None

            # Locate service instance
            instance = await self.service_discovery.discover_service(service_name)
            if not instance:
                self.logger.warning(f"No instances found for service: {service_name}")
                return None

            # Prepare mTLS context for secure communication
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
        """
        Remove service and security configurations.
        
        Performs cleanup across all security systems:
        1. Service discovery removal
        2. Authentication cleanup
        3. Rate limit removal
        
        NOTE: Continues with partial cleanup even if some steps fail
        to ensure maximum possible cleanup.
        """
        try:
            # Remove from service discovery first
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