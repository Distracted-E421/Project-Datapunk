from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass
import jwt
import re
from datetime import datetime, timedelta
from enum import Enum
import ipaddress
from .mtls import MTLSConfig
from ...auth.core.access_control import AccessControl
from ...monitoring import MetricsCollector  # We'll implement this later

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    required_claims: List[str] = None
    allowed_algorithms: List[str] = None
    allowed_issuers: List[str] = None
    allowed_audiences: List[str] = None
    max_token_age: timedelta = timedelta(hours=1)
    require_mtls: bool = True
    allowed_ip_ranges: List[str] = None
    rate_limit: Optional[int] = None  # requests per minute
    security_level: SecurityLevel = SecurityLevel.MEDIUM

class SecurityContext:
    """Holds security-related information for a request"""
    def __init__(
        self,
        token: Optional[str] = None,
        mtls_config: Optional[MTLSConfig] = None,
        client_ip: Optional[str] = None,
        request_metadata: Optional[Dict[str, Any]] = None
    ):
        self.token = token
        self.mtls_config = mtls_config
        self.client_ip = client_ip
        self.metadata = request_metadata or {}
        self.validated_claims = {}
        self.security_level = SecurityLevel.LOW
        self.validation_errors = []

class SecurityValidator:
    """Handles security validation and policy enforcement"""
    def __init__(
        self,
        policy: SecurityPolicy,
        access_control: AccessControl,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.policy = policy
        self.access_control = access_control
        self.metrics = metrics_collector
        self._token_blacklist = set()
        
    async def validate_request(self, context: SecurityContext) -> bool:
        """Validate a request against security policies"""
        try:
            validations = [
                self._validate_token(context),
                self._validate_mtls(context),
                self._validate_ip(context),
                self._validate_rate_limit(context)
            ]
            
            results = await asyncio.gather(*validations, return_exceptions=True)
            
            # Check for validation failures
            for result in results:
                if isinstance(result, Exception):
                    context.validation_errors.append(str(result))
                elif not result:
                    return False
                    
            # Update metrics
            if self.metrics:
                await self.metrics.increment("security.validations.success")
                
            return True
            
        except Exception as e:
            if self.metrics:
                await self.metrics.increment("security.validations.failure")
            context.validation_errors.append(str(e))
            return False

    async def _validate_token(self, context: SecurityContext) -> bool:
        """Validate JWT token"""
        if not context.token:
            if self.policy.security_level == SecurityLevel.LOW:
                return True
            raise SecurityValidationError("Token required")
            
        if context.token in self._token_blacklist:
            raise SecurityValidationError("Token has been blacklisted")
            
        try:
            claims = jwt.decode(
                context.token,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": bool(self.policy.allowed_audiences),
                    "verify_iss": bool(self.policy.allowed_issuers)
                }
            )
            
            # Validate required claims
            if self.policy.required_claims:
                missing_claims = set(self.policy.required_claims) - set(claims.keys())
                if missing_claims:
                    raise SecurityValidationError(f"Missing required claims: {missing_claims}")
                    
            # Validate token age
            if "iat" in claims:
                issued_at = datetime.fromtimestamp(claims["iat"])
                if datetime.utcnow() - issued_at > self.policy.max_token_age:
                    raise SecurityValidationError("Token has exceeded maximum age")
                    
            context.validated_claims = claims
            return True
            
        except jwt.InvalidTokenError as e:
            raise SecurityValidationError(f"Token validation failed: {str(e)}")

    async def _validate_mtls(self, context: SecurityContext) -> bool:
        """Validate MTLS configuration"""
        if not self.policy.require_mtls:
            return True
            
        if not context.mtls_config:
            raise SecurityValidationError("MTLS configuration required")
            
        try:
            # Validate certificate chain
            MTLSConfig._validate_certificate_chain(
                context.mtls_config.certificate,
                context.mtls_config.ca_cert
            )
            return True
        except Exception as e:
            raise SecurityValidationError(f"MTLS validation failed: {str(e)}")

    async def _validate_ip(self, context: SecurityContext) -> bool:
        """Validate client IP against allowed ranges"""
        if not self.policy.allowed_ip_ranges:
            return True
            
        if not context.client_ip:
            raise SecurityValidationError("Client IP required for validation")
            
        try:
            client_ip = ipaddress.ip_address(context.client_ip)
            for allowed_range in self.policy.allowed_ip_ranges:
                network = ipaddress.ip_network(allowed_range)
                if client_ip in network:
                    return True
            raise SecurityValidationError("Client IP not in allowed ranges")
        except ValueError as e:
            raise SecurityValidationError(f"IP validation failed: {str(e)}")

    async def _validate_rate_limit(self, context: SecurityContext) -> bool:
        """Validate request against rate limits"""
        if not self.policy.rate_limit:
            return True
            
        # This would typically use Redis or similar for distributed rate limiting
        # For now, we'll just return True
        return True

    def blacklist_token(self, token: str):
        """Add a token to the blacklist"""
        self._token_blacklist.add(token)

class SecurityValidationError(Exception):
    """Custom exception for security validation failures"""
    pass 