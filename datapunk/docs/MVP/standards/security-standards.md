# Security Standards

## Purpose

Define comprehensive security standards for authentication, authorization, and data protection across the Datapunk platform.

## Context

Security is implemented at multiple layers:

1. Service-to-service communication (mTLS)
2. External API access (OAuth2, JWT)
3. Data protection (encryption, access control)
4. Audit logging and compliance

## Design/Details

### 1. Authentication Layers

```yaml
authentication_layers:
  service_mesh:
    type: "mTLS"
    certificate_authority: "internal"
    cert_rotation: "30d"
    validation:
      - "certificate_chain"
      - "hostname_verification"
      - "revocation_check"
    
  external_api:
    primary: "OAuth2"
    secondary: "API Key"
    jwt:
      algorithm: "RS256"
      expiry: "1h"
      refresh_window: "24h"
    
  internal_services:
    type: "service_token"
    rotation: "7d"
    scope_based: true
```

### 2. Authorization Framework

```yaml
authorization:
  rbac:
    enabled: true
    default_deny: true
    roles:
      - name: "admin"
        permissions: ["*"]
      - name: "service"
        permissions: ["read", "write"]
      - name: "readonly"
        permissions: ["read"]
    
  service_policies:
    nexus:
      - action: "route"
        resource: "*"
    lake:
      - action: "write"
        resource: "data/*"
    stream:
      - action: "publish"
        resource: "events/*"
```

### 3. mTLS Configuration

```yaml
mtls_config:
  certificate_authority:
    type: "vault"
    path: "pki/datapunk"
    max_ttl: "720h"
    
  certificates:
    format: "x509"
    key_type: "RSA"
    key_bits: 2048
    
  validation:
    ocsp_enabled: true
    crl_check: true
    verify_client: true
```

### 4. Data Protection

```yaml
data_protection:
  encryption:
    at_rest:
      algorithm: "AES-256-GCM"
      key_rotation: "90d"
      
    in_transit:
      protocol: "TLS 1.3"
      cipher_suites:
        - "TLS_AES_256_GCM_SHA384"
        - "TLS_CHACHA20_POLY1305_SHA256"
      
  sensitive_data:
    pii:
      detection: true
      encryption: true
      masking: true
    secrets:
      vault_integration: true
      auto_rotation: true
```

## Implementation Patterns

### 1. Service Authentication

```python
from typing import Optional
from cryptography import x509
from cryptography.hazmat.primitives import hashes
import structlog

logger = structlog.get_logger()

class MTLSAuthenticator:
    def __init__(self, ca_cert_path: str):
        self.ca_cert_path = ca_cert_path
        self.logger = logger.bind(component="mtls_auth")
        
    async def authenticate_service(self,
                                 cert: x509.Certificate,
                                 expected_service: str) -> bool:
        """Authenticate service using mTLS certificate."""
        try:
            # Verify certificate chain
            if not self.verify_certificate_chain(cert):
                return False
            
            # Verify service identity
            service_name = self.extract_service_name(cert)
            if service_name != expected_service:
                self.logger.warning("service_name_mismatch",
                                  expected=expected_service,
                                  received=service_name)
                return False
            
            # Verify not revoked
            if self.is_certificate_revoked(cert):
                return False
                
            return True
            
        except Exception as e:
            self.logger.error("authentication_failed",
                            error=str(e))
            return False
```

### 2. API Authentication

```python
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt

class APIAuthenticator:
    def __init__(self, 
                 private_key: str,
                 public_key: str,
                 algorithm: str = "RS256"):
        self.private_key = private_key
        self.public_key = public_key
        self.algorithm = algorithm
    
    def generate_token(self,
                      subject: str,
                      scopes: List[str],
                      expiry: timedelta = timedelta(hours=1)) -> str:
        """Generate JWT token."""
        now = datetime.utcnow()
        payload = {
            "sub": subject,
            "scopes": scopes,
            "iat": now,
            "exp": now + expiry,
            "iss": "datapunk"
        }
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)
    
    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
                issuer="datapunk"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise SecurityError("Token expired")
        except jwt.InvalidTokenError as e:
            raise SecurityError(f"Invalid token: {str(e)}")
```

### 3. Authorization

```python
from enum import Enum
from typing import List, Set
from dataclasses import dataclass

class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

@dataclass
class Role:
    name: str
    permissions: Set[Permission]

class Authorizer:
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        
    def add_role(self, role: Role):
        """Add role definition."""
        self.roles[role.name] = role
        
    def check_permission(self,
                        user_roles: List[str],
                        required_permission: Permission) -> bool:
        """Check if user has required permission."""
        user_permissions = set()
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role:
                user_permissions.update(role.permissions)
                
        return required_permission in user_permissions
```

### 4. Audit Logging

```python
from datetime import datetime
from typing import Optional, Any
import structlog

logger = structlog.get_logger()

class SecurityAuditLogger:
    def __init__(self):
        self.logger = logger.bind(component="security_audit")
        
    def log_auth_attempt(self,
                        subject: str,
                        success: bool,
                        method: str,
                        ip_address: str,
                        details: Optional[Dict] = None):
        """Log authentication attempt."""
        self.logger.info("auth_attempt",
                        subject=subject,
                        success=success,
                        method=method,
                        ip_address=ip_address,
                        **details or {})
        
    def log_access(self,
                   subject: str,
                   resource: str,
                   action: str,
                   success: bool,
                   reason: Optional[str] = None):
        """Log resource access attempt."""
        self.logger.info("resource_access",
                        subject=subject,
                        resource=resource,
                        action=action,
                        success=success,
                        reason=reason)
```

## Security Monitoring

```yaml
security_monitoring:
  metrics:
    authentication:
      - name: "auth_attempts_total"
        labels: ["method", "success"]
      - name: "token_validation_errors"
        labels: ["error_type"]
        
    authorization:
      - name: "permission_checks_total"
        labels: ["role", "permission", "granted"]
      - name: "unauthorized_access_attempts"
        labels: ["resource", "action"]
        
    certificates:
      - name: "cert_validation_errors"
        labels: ["error_type"]
      - name: "cert_expiry_days"
        labels: ["service"]
```

## Known Issues and Mitigations

### 1. Certificate Management

```python
class CertificateManager:
    async def rotate_certificate(self,
                               service: str,
                               current_cert: x509.Certificate) -> None:
        """Rotate service certificate."""
        try:
            # Generate new certificate
            new_cert = await self.generate_certificate(service)
            
            # Update service configuration
            await self.update_service_cert(service, new_cert)
            
            # Verify new certificate
            if not await self.verify_certificate(new_cert):
                await self.rollback_certificate(service, current_cert)
                
        except Exception as e:
            self.logger.error("cert_rotation_failed",
                            service=service,
                            error=str(e))
            raise
```

### 2. Token Revocation

```python
class TokenManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        
    async def revoke_token(self, token: str, reason: str):
        """Revoke active token."""
        try:
            # Add to blacklist
            await self.redis.setex(
                f"revoked_token:{token}",
                3600,  # TTL matching token max age
                reason
            )
            
            # Notify all services
            await self.broadcast_revocation(token)
            
        except Exception as e:
            self.logger.error("token_revocation_failed",
                            error=str(e))
            raise
```

## Testing Requirements

```yaml
security_testing:
  authentication:
    - valid_credentials
    - invalid_credentials
    - expired_certificates
    - revoked_tokens
    
  authorization:
    - permission_checks
    - role_inheritance
    - resource_access
    
  encryption:
    - data_encryption
    - key_rotation
    - secure_communication
```
