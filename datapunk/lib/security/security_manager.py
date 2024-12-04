import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import jwt
import hashlib
import secrets
from enum import Enum
import re
from cryptography.fernet import Fernet
import base64
from threading import Lock

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ResourceType(Enum):
    API = "api"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    MEMORY = "memory"

@dataclass
class SecurityPolicy:
    name: str
    level: SecurityLevel
    resource_types: Set[ResourceType]
    max_attempts: int = 3
    lockout_duration: int = 300  # seconds
    require_mfa: bool = False
    encryption_required: bool = True
    audit_logging: bool = True

@dataclass
class SecurityEvent:
    timestamp: datetime
    event_type: str
    resource_type: ResourceType
    severity: SecurityLevel
    description: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict] = None

class SecurityManager:
    def __init__(
        self,
        default_policy: Optional[SecurityPolicy] = None,
        jwt_secret: Optional[str] = None,
        encryption_key: Optional[bytes] = None
    ):
        self.policies: Dict[str, SecurityPolicy] = {}
        self.default_policy = default_policy or SecurityPolicy(
            name="default",
            level=SecurityLevel.MEDIUM,
            resource_types={ResourceType.API},
            require_mfa=False
        )
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(32)
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        self.security_events: List[SecurityEvent] = []
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()

    def add_policy(self, policy: SecurityPolicy) -> None:
        """Add a new security policy."""
        with self._lock:
            self.policies[policy.name] = policy
            self.logger.info(f"Added security policy: {policy.name}")

    def validate_access(
        self,
        resource_type: ResourceType,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        security_level: Optional[SecurityLevel] = None
    ) -> bool:
        """Validate access based on security policies."""
        with self._lock:
            # Check IP blocking
            if source_ip and self._is_ip_blocked(source_ip):
                self._log_security_event(
                    SecurityEvent(
                        timestamp=datetime.now(),
                        event_type="access_denied",
                        resource_type=resource_type,
                        severity=SecurityLevel.HIGH,
                        description="Access attempt from blocked IP",
                        source_ip=source_ip,
                        user_id=user_id
                    )
                )
                return False

            # Get applicable policy
            policy = self._get_applicable_policy(resource_type, security_level)

            # Validate against policy
            if policy.require_mfa and not self._verify_mfa(user_id):
                self._record_failed_attempt(source_ip)
                return False

            return True

    def generate_token(
        self,
        user_id: str,
        expiration: timedelta = timedelta(hours=1),
        additional_claims: Optional[Dict] = None
    ) -> str:
        """Generate a JWT token."""
        claims = {
            'user_id': user_id,
            'exp': datetime.utcnow() + expiration,
            'iat': datetime.utcnow()
        }
        if additional_claims:
            claims.update(additional_claims)

        return jwt.encode(claims, self.jwt_secret, algorithm='HS256')

    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate a JWT token."""
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token: {str(e)}")
            return None

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt encrypted data."""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {str(e)}")
            raise

    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP is blocked."""
        if ip in self.blocked_ips:
            block_time = self.blocked_ips[ip]
            if datetime.now() - block_time > timedelta(seconds=self.default_policy.lockout_duration):
                del self.blocked_ips[ip]
                return False
            return True
        return False

    def _record_failed_attempt(self, ip: Optional[str]) -> None:
        """Record a failed access attempt."""
        if not ip:
            return

        current_time = datetime.now()
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = []

        # Clean up old attempts
        self.failed_attempts[ip] = [
            attempt for attempt in self.failed_attempts[ip]
            if current_time - attempt < timedelta(seconds=self.default_policy.lockout_duration)
        ]

        self.failed_attempts[ip].append(current_time)

        # Check if should block
        if len(self.failed_attempts[ip]) >= self.default_policy.max_attempts:
            self.blocked_ips[ip] = current_time
            self.logger.warning(f"IP {ip} blocked due to multiple failed attempts")

    def _get_applicable_policy(
        self,
        resource_type: ResourceType,
        security_level: Optional[SecurityLevel] = None
    ) -> SecurityPolicy:
        """Get the applicable security policy."""
        # Find most restrictive policy that matches
        applicable_policies = [
            policy for policy in self.policies.values()
            if resource_type in policy.resource_types
            and (not security_level or policy.level == security_level)
        ]

        if not applicable_policies:
            return self.default_policy

        return max(applicable_policies, key=lambda p: p.level.value)

    def _verify_mfa(self, user_id: Optional[str]) -> bool:
        """Verify MFA for a user."""
        # This is a placeholder - implement actual MFA verification
        return True

    def _log_security_event(self, event: SecurityEvent) -> None:
        """Log a security event."""
        self.security_events.append(event)
        self.logger.warning(
            f"Security event: {event.event_type} - {event.description}"
        )

    def get_security_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_severity: Optional[SecurityLevel] = None
    ) -> List[SecurityEvent]:
        """Get filtered security events."""
        events = self.security_events

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        if min_severity:
            events = [e for e in events if e.severity.value >= min_severity.value]

        return sorted(events, key=lambda e: e.timestamp, reverse=True)

    def analyze_security_patterns(self) -> Dict:
        """Analyze security events for patterns."""
        analysis = {
            'total_events': len(self.security_events),
            'events_by_type': {},
            'events_by_severity': {},
            'top_source_ips': {},
            'suspicious_patterns': []
        }

        for event in self.security_events:
            # Count by type
            analysis['events_by_type'][event.event_type] = (
                analysis['events_by_type'].get(event.event_type, 0) + 1
            )

            # Count by severity
            analysis['events_by_severity'][event.severity.value] = (
                analysis['events_by_severity'].get(event.severity.value, 0) + 1
            )

            # Track source IPs
            if event.source_ip:
                analysis['top_source_ips'][event.source_ip] = (
                    analysis['top_source_ips'].get(event.source_ip, 0) + 1
                )

        # Identify suspicious patterns
        for ip, count in analysis['top_source_ips'].items():
            if count > self.default_policy.max_attempts * 2:
                analysis['suspicious_patterns'].append({
                    'type': 'high_failure_rate',
                    'source_ip': ip,
                    'count': count,
                    'description': f"High number of security events from IP {ip}"
                })

        return analysis 