from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
import asyncio
from datetime import datetime, timedelta
import jwt
from enum import Enum
import re
import ipaddress
from .mtls import MTLSManager
from ..monitoring import MetricsCollector

class SecurityLevel(Enum):
    """Security levels for policies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ValidationType(Enum):
    """Types of security validation"""
    TOKEN = "token"
    MTLS = "mtls"
    IP = "ip"
    RATE_LIMIT = "rate_limit"
    SCOPE = "scope"
    ROLE = "role"

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    required_validations: Set[ValidationType]
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    token_required: bool = True
    mtls_required: bool = False
    allowed_ips: Optional[List[str]] = None
    allowed_roles: Optional[List[str]] = None
    required_scopes: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    max_token_age: Optional[int] = None  # seconds
    enable_jwt: bool = True
    jwt_algorithms: List[str] = field(default_factory=lambda: ["HS256", "RS256"])
    jwt_audience: Optional[str] = None
    jwt_issuer: Optional[str] = None

@dataclass
class SecurityContext:
    """Context for security validation"""
    token: Optional[str] = None
    client_ip: Optional[str] = None
    request_metadata: Optional[Dict[str, Any]] = None
    mtls_cert: Optional[bytes] = None
    validation_errors: List[str] = field(default_factory=list)
    validated_claims: Dict[str, Any] = field(default_factory=dict)

class ValidationError(Exception):
    """Base class for validation errors"""
    pass

class TokenValidationError(ValidationError):
    """Token validation errors"""
    pass

class SecurityValidator:
    """Handles security validation and policy enforcement"""
    def __init__(
        self,
        policy: SecurityPolicy,
        mtls_manager: Optional[MTLSManager] = None,
        metrics_collector: Optional[MetricsCollector] = None,
        jwt_secret: Optional[str] = None,
        jwt_public_key: Optional[str] = None
    ):
        self.policy = policy
        self.mtls_manager = mtls_manager
        self.metrics = metrics_collector
        self.jwt_secret = jwt_secret
        self.jwt_public_key = jwt_public_key
        self._token_blacklist: Set[str] = set()
        self._rate_limits: Dict[str, List[datetime]] = {}

    async def validate_request(self, context: SecurityContext) -> bool:
        """Validate request against security policy"""
        try:
            # Reset validation state
            context.validation_errors = []
            context.validated_claims = {}

            # Perform required validations
            for validation_type in self.policy.required_validations:
                await self._validate_by_type(validation_type, context)

            if self.metrics:
                await self.metrics.increment(
                    "security.validation.success",
                    tags={"level": self.policy.security_level.value}
                )

            return not context.validation_errors

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "security.validation.error",
                    tags={
                        "level": self.policy.security_level.value,
                        "error": str(e)
                    }
                )
            context.validation_errors.append(str(e))
            return False

    async def _validate_by_type(
        self,
        validation_type: ValidationType,
        context: SecurityContext
    ):
        """Perform specific type of validation"""
        try:
            if validation_type == ValidationType.TOKEN:
                await self._validate_token(context)
            elif validation_type == ValidationType.MTLS:
                await self._validate_mtls(context)
            elif validation_type == ValidationType.IP:
                await self._validate_ip(context)
            elif validation_type == ValidationType.RATE_LIMIT:
                await self._validate_rate_limit(context)
            elif validation_type == ValidationType.SCOPE:
                await self._validate_scope(context)
            elif validation_type == ValidationType.ROLE:
                await self._validate_role(context)

        except ValidationError as e:
            context.validation_errors.append(str(e))
            if self.metrics:
                await self.metrics.increment(
                    "security.validation.failure",
                    tags={
                        "type": validation_type.value,
                        "error": str(e)
                    }
                )

    async def _validate_token(self, context: SecurityContext):
        """Validate authentication token"""
        if not context.token and self.policy.token_required:
            raise TokenValidationError("Missing required token")

        if context.token in self._token_blacklist:
            raise TokenValidationError("Token is blacklisted")

        if self.policy.enable_jwt and context.token:
            try:
                # Verify JWT
                if self.jwt_public_key:
                    claims = jwt.decode(
                        context.token,
                        self.jwt_public_key,
                        algorithms=self.policy.jwt_algorithms,
                        audience=self.policy.jwt_audience,
                        issuer=self.policy.jwt_issuer
                    )
                else:
                    claims = jwt.decode(
                        context.token,
                        self.jwt_secret,
                        algorithms=self.policy.jwt_algorithms,
                        audience=self.policy.jwt_audience,
                        issuer=self.policy.jwt_issuer
                    )

                # Check token age
                if self.policy.max_token_age:
                    issued_at = claims.get("iat")
                    if issued_at:
                        age = datetime.utcnow().timestamp() - issued_at
                        if age > self.policy.max_token_age:
                            raise TokenValidationError("Token has expired")

                context.validated_claims = claims

            except jwt.InvalidTokenError as e:
                raise TokenValidationError(f"Invalid JWT token: {str(e)}")

    async def _validate_mtls(self, context: SecurityContext):
        """Validate mutual TLS certificate"""
        if self.policy.mtls_required:
            if not context.mtls_cert:
                raise ValidationError("Missing required mTLS certificate")

            if not self.mtls_manager:
                raise ValidationError("mTLS manager not configured")

            if not self.mtls_manager.verify_peer_certificate(context.mtls_cert):
                raise ValidationError("Invalid mTLS certificate")

    async def _validate_ip(self, context: SecurityContext):
        """Validate client IP address"""
        if self.policy.allowed_ips and context.client_ip:
            ip = ipaddress.ip_address(context.client_ip)
            allowed = False
            for allowed_ip in self.policy.allowed_ips:
                network = ipaddress.ip_network(allowed_ip)
                if ip in network:
                    allowed = True
                    break
            if not allowed:
                raise ValidationError(f"IP {context.client_ip} not allowed")

    async def _validate_rate_limit(self, context: SecurityContext):
        """Validate rate limits"""
        if self.policy.rate_limit:
            key = context.client_ip or "anonymous"
            now = datetime.utcnow()
            
            # Clean up old requests
            self._rate_limits[key] = [
                t for t in self._rate_limits.get(key, [])
                if now - t < timedelta(minutes=1)
            ]
            
            # Check rate limit
            if len(self._rate_limits[key]) >= self.policy.rate_limit:
                raise ValidationError("Rate limit exceeded")
                
            # Record request
            self._rate_limits[key].append(now)

    async def _validate_scope(self, context: SecurityContext):
        """Validate token scopes"""
        if self.policy.required_scopes:
            token_scopes = context.validated_claims.get("scope", "").split()
            missing_scopes = set(self.policy.required_scopes) - set(token_scopes)
            if missing_scopes:
                raise ValidationError(
                    f"Missing required scopes: {', '.join(missing_scopes)}"
                )

    async def _validate_role(self, context: SecurityContext):
        """Validate user roles"""
        if self.policy.allowed_roles:
            token_roles = context.validated_claims.get("roles", [])
            if not any(role in self.policy.allowed_roles for role in token_roles):
                raise ValidationError("Insufficient role permissions")

    async def blacklist_token(self, token: str):
        """Add token to blacklist"""
        self._token_blacklist.add(token)
        if self.metrics:
            await self.metrics.increment("security.token.blacklisted")

    async def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            "blacklisted_tokens": len(self._token_blacklist),
            "rate_limited_ips": len(self._rate_limits),
            "security_level": self.policy.security_level.value,
            "required_validations": [v.value for v in self.policy.required_validations]
        } 