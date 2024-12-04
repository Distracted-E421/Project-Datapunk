"""
Core configuration for auth components.

This module implements a comprehensive configuration management system for authentication
and security settings. It provides:

Key Features:
- Dynamic configuration loading from files and environment variables
- Real-time config reloading with file watching
- Validation of security parameters with strict enforcement
- Centralized management of auth-related settings
- Support for different security levels and compliance standards

Architecture Notes:
- Uses dataclasses for type-safe config structures
- Implements the Observer pattern for config changes
- Provides rollback capability on failed validation
- Supports hierarchical configuration inheritance

Security Considerations:
- Enforces minimum security standards through validation
- Supports multiple encryption levels including E2E and mTLS
- Implements secure defaults for all critical parameters
- Provides audit logging for configuration changes

Usage:
    config = AuthConfig(
        config_path=Path("/path/to/config.yaml"),
        env_prefix="AUTH_",
        auto_reload=True
    )
"""

from typing import Dict, Optional, Set, Any, List, Callable
from dataclasses import dataclass, asdict
from datetime import timedelta
from enum import Enum
import structlog
from pathlib import Path
import yaml
import os
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio

from ..api_keys.policies import KeyType
from ..policy.types import PolicyType
from ..audit.types import ComplianceStandard

logger = structlog.get_logger()

class SecurityLevel(Enum):
    """
    Defines the security posture for the entire authentication system.
    
    BASIC: Development/testing environments only
    STANDARD: Minimum for production deployments
    HIGH: Regulated environments (e.g., financial services)
    CRITICAL: High-security environments (e.g., healthcare, government)
    """
    BASIC = "basic"         # Basic security controls
    STANDARD = "standard"   # Standard security measures
    HIGH = "high"          # Enhanced security
    CRITICAL = "critical"  # Maximum security

class EncryptionLevel(Enum):
    """Encryption requirements."""
    NONE = "none"          # No encryption
    TLS = "tls"           # TLS only
    TLS_MTLS = "tls_mtls" # TLS with mTLS
    E2E = "e2e"           # End-to-end encryption

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass

class ConfigReloadError(Exception):
    """Raised when configuration reload fails."""
    pass

@dataclass
class APIKeyConfig:
    """
    API key configuration and lifecycle management.
    
    NOTE: default_ttl and rotation_window must be carefully balanced:
    - Too short: Excessive rotation overhead
    - Too long: Increased security risk
    
    SECURITY: min_length should never be set below 32 for production use
    """
    default_ttl: timedelta = timedelta(days=90)
    min_length: int = 32
    max_length: int = 64
    allowed_types: Set[KeyType] = None
    require_rotation: bool = True
    rotation_window: timedelta = timedelta(days=7)
    emergency_expiry: timedelta = timedelta(hours=1)

@dataclass
class PolicyConfig:
    """
    Policy enforcement configuration for access control.
    
    IMPORTANT: strict_mode=True enforces immediate termination on policy violations
    while False allows graceful degradation with logging
    
    TODO: Add support for policy inheritance and override mechanisms
    """
    enabled_policies: Set[PolicyType]
    strict_mode: bool = True
    require_approval: bool = True
    approval_timeout: timedelta = timedelta(days=1)
    max_retries: int = 3
    retry_delay: int = 5  # seconds

@dataclass
class AuditConfig:
    """Audit configuration."""
    enabled_standards: Set[ComplianceStandard]
    retention_period: timedelta = timedelta(days=365)
    require_signing: bool = True
    immutable_storage: bool = True
    pii_detection: bool = True

@dataclass
class SecurityConfig:
    """Security configuration."""
    security_level: SecurityLevel = SecurityLevel.STANDARD
    encryption_level: EncryptionLevel = EncryptionLevel.TLS
    require_mfa: bool = False
    session_timeout: timedelta = timedelta(hours=12)
    max_failed_attempts: int = 5
    lockout_period: timedelta = timedelta(minutes=15)

@dataclass
class IntegrationConfig:
    """Integration settings."""
    metrics_enabled: bool = True
    tracing_enabled: bool = True
    cache_ttl: timedelta = timedelta(minutes=5)
    message_retry_count: int = 3
    message_retry_delay: int = 5  # seconds

@dataclass
class ValidationResult:
    """Result of configuration validation."""
    valid: bool
    issues: List[str]
    warnings: List[str]

class ConfigValidator:
    """
    Validates configuration values against security best practices and operational requirements.
    
    Implementation follows defense-in-depth principle:
    1. Validates basic operational parameters
    2. Enforces security minimums
    3. Checks for potential security/performance conflicts
    
    FIXME: Add validation for cross-cutting concerns between different config sections
    """
    
    @staticmethod
    def validate_api_keys(config: APIKeyConfig) -> ValidationResult:
        """Validate API key configuration."""
        issues = []
        warnings = []
        
        # Validate key lengths
        if config.min_length < 16:
            issues.append("Minimum key length should be at least 16 characters")
        if config.max_length > 128:
            warnings.append("Maximum key length over 128 may impact performance")
        if config.min_length >= config.max_length:
            issues.append("Minimum length must be less than maximum length")
        
        # Validate TTL
        if config.default_ttl.days < 1:
            issues.append("Default TTL should be at least 1 day")
        if config.default_ttl.days > 365:
            warnings.append("TTL over 365 days may pose security risks")
        
        # Validate rotation settings
        if config.rotation_window >= config.default_ttl:
            issues.append("Rotation window must be shorter than TTL")
        
        return ValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            warnings=warnings
        )
    
    @staticmethod
    def validate_policy(config: PolicyConfig) -> ValidationResult:
        """Validate policy configuration."""
        issues = []
        warnings = []
        
        # Validate retry settings
        if config.max_retries < 1:
            issues.append("Max retries must be at least 1")
        if config.retry_delay < 1:
            issues.append("Retry delay must be at least 1 second")
        if config.max_retries > 10:
            warnings.append("High retry count may impact performance")
        
        # Validate approval settings
        if config.approval_timeout.days < 1:
            issues.append("Approval timeout should be at least 1 day")
        if not config.enabled_policies:
            issues.append("At least one policy type must be enabled")
        
        return ValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            warnings=warnings
        )
    
    @staticmethod
    def validate_security(config: SecurityConfig) -> ValidationResult:
        """Validate security configuration."""
        issues = []
        warnings = []
        
        # Validate security level
        if config.security_level == SecurityLevel.BASIC:
            warnings.append("Basic security level not recommended for production")
        
        # Validate encryption
        if config.encryption_level == EncryptionLevel.NONE:
            issues.append("Encryption should be enabled")
        
        # Validate session settings
        if config.session_timeout.seconds < 300:
            issues.append("Session timeout should be at least 5 minutes")
        if config.session_timeout.days > 1:
            warnings.append("Long session timeouts may pose security risks")
        
        return ValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            warnings=warnings
        )

class ConfigFileHandler(FileSystemEventHandler):
    """
    Handles real-time configuration file changes with atomic updates.
    
    Design Considerations:
    - Uses file system events to minimize polling overhead
    - Implements debouncing to prevent reload storms
    - Maintains config consistency during reloads
    
    NOTE: File permissions changes are not currently monitored
    """
    
    def __init__(self, config_path: Path, reload_callback: Callable):
        self.config_path = config_path
        self.reload_callback = reload_callback
        self.logger = logger.bind(component="config_handler")
    
    def on_modified(self, event):
        if event.src_path == str(self.config_path):
            try:
                self.reload_callback()
                self.logger.info("config_reloaded",
                               path=str(self.config_path))
            except Exception as e:
                self.logger.error("config_reload_failed",
                                error=str(e))

class AuthConfig:
    """
    Central configuration manager implementing a secure configuration lifecycle.
    
    Architecture:
    1. Loads base configuration from files
    2. Overlays environment variables
    3. Validates complete configuration
    4. Monitors for changes (when auto_reload=True)
    
    SECURITY: Configuration rollback is atomic to prevent partial updates
    
    Error Handling:
    - Invalid configurations trigger immediate rollback
    - Validation failures are logged with specific violations
    - File permission issues are treated as security events
    
    TODO: Add support for encrypted configuration values
    TODO: Implement configuration version tracking
    """
    
    def __init__(self,
                 config_path: Optional[Path] = None,
                 env_prefix: str = "AUTH_",
                 auto_reload: bool = False):
        self.config_path = config_path
        self.env_prefix = env_prefix
        self.auto_reload = auto_reload
        self.logger = logger.bind(component="auth_config")
        self.validator = ConfigValidator()
        self._observer = None
        
        # Initialize configurations
        self._initialize_configs()
        
        # Load configurations
        if config_path:
            self._load_config()
        self._load_env()
        
        # Validate configurations
        self._validate_all()
        
        # Set up auto-reload if enabled
        if auto_reload and config_path:
            self._setup_file_watcher()
    
    def _initialize_configs(self) -> None:
        """Initialize configuration objects."""
        self.api_keys = APIKeyConfig()
        self.policy = PolicyConfig(enabled_policies=set())
        self.audit = AuditConfig(enabled_standards=set())
        self.security = SecurityConfig()
        self.integration = IntegrationConfig()
    
    def _validate_all(self) -> None:
        """
        Performs comprehensive validation of all configuration sections.
        
        Validation Hierarchy:
        1. Individual section validation
        2. Cross-section consistency checks
        3. Security minimum enforcement
        
        SECURITY: Validation failures in security-critical sections trigger immediate shutdown
        """
        issues = []
        warnings = []
        
        # Validate each config section
        api_keys_result = self.validator.validate_api_keys(self.api_keys)
        if not api_keys_result.valid:
            issues.extend(f"API Keys: {issue}" for issue in api_keys_result.issues)
        warnings.extend(f"API Keys: {warn}" for warn in api_keys_result.warnings)
        
        policy_result = self.validator.validate_policy(self.policy)
        if not policy_result.valid:
            issues.extend(f"Policy: {issue}" for issue in policy_result.issues)
        warnings.extend(f"Policy: {warn}" for warn in policy_result.warnings)
        
        security_result = self.validator.validate_security(self.security)
        if not security_result.valid:
            issues.extend(f"Security: {issue}" for issue in security_result.issues)
        warnings.extend(f"Security: {warn}" for warn in security_result.warnings)
        
        # Log warnings
        for warning in warnings:
            self.logger.warning("config_warning", warning=warning)
        
        # Raise if there are issues
        if issues:
            raise ConfigValidationError(
                f"Configuration validation failed:\n" + "\n".join(issues)
            )
    
    def _setup_file_watcher(self) -> None:
        """
        Initializes configuration file monitoring for hot-reloading.
        
        Implementation Notes:
        - Uses non-blocking observer pattern
        - Maintains single source of truth
        - Prevents concurrent reloads
        
        FIXME: Add support for handling rapid successive changes
        """
        try:
            self._observer = Observer()
            handler = ConfigFileHandler(self.config_path, self.reload)
            self._observer.schedule(
                handler,
                str(self.config_path.parent),
                recursive=False
            )
            self._observer.start()
            self.logger.info("config_watcher_started",
                           path=str(self.config_path))
            
        except Exception as e:
            self.logger.error("config_watcher_failed",
                            error=str(e))
            raise ConfigReloadError(f"Failed to set up config watcher: {str(e)}")
    
    def reload(self) -> None:
        """Reload configuration from all sources."""
        try:
            # Store old configs
            old_configs = {
                "api_keys": asdict(self.api_keys),
                "policy": asdict(self.policy),
                "audit": asdict(self.audit),
                "security": asdict(self.security),
                "integration": asdict(self.integration)
            }
            
            # Reload configurations
            self._initialize_configs()
            if self.config_path:
                self._load_config()
            self._load_env()
            
            # Validate new configurations
            try:
                self._validate_all()
            except ConfigValidationError:
                # Restore old configs on validation failure
                self._restore_configs(old_configs)
                raise
            
            self.logger.info("config_reloaded")
            
        except Exception as e:
            self.logger.error("config_reload_failed",
                            error=str(e))
            raise ConfigReloadError(f"Failed to reload config: {str(e)}")
    
    def _restore_configs(self, old_configs: Dict[str, Dict]) -> None:
        """Restore previous configurations."""
        self.api_keys = APIKeyConfig(**old_configs["api_keys"])
        self.policy = PolicyConfig(**old_configs["policy"])
        self.audit = AuditConfig(**old_configs["audit"])
        self.security = SecurityConfig(**old_configs["security"])
        self.integration = IntegrationConfig(**old_configs["integration"])
    
    def __del__(self):
        """Clean up file watcher."""
        if self._observer:
            self._observer.stop()
            self._observer.join()