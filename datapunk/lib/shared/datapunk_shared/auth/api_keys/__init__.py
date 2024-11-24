"""
API Key Management System
------------------------
A comprehensive framework for managing API keys with features for security,
compliance, rotation, validation, and notifications. This system is designed
to meet enterprise-grade security requirements while maintaining flexibility
for different use cases.

Key Components:
- Key Management: Core CRUD operations and lifecycle management
- Policy Enforcement: Security controls and resource quotas
- Key Rotation: Automated and manual key rotation with configurable policies
- Validation: Real-time and periodic key validation
- Notifications: Multi-channel alerting for key events

Integration Dependencies:
- MetricsClient: For monitoring key usage and performance
- CacheClient: For temporary key storage and validation caching
- MessageBroker: For distributed key event notifications

Security Note: This module implements defense-in-depth strategies through
multiple validation layers and strict policy enforcement. All key operations
are logged and audited for compliance purposes.
"""

from typing import TYPE_CHECKING

# Core key management functionality
from .manager import APIKeyManager

# Policy enforcement and security controls
from .policies import (
    KeyType, KeyPolicy, ComplianceRequirements,
    SecurityControls, ResourceQuota, TimeWindow,
    CircuitBreaker
)

# Automated and manual key rotation management
from .rotation import (
    KeyRotationManager, RotationReason, RotationConfig
)

# Key validation and verification
from .validation import KeyValidator, KeyValidationConfig

# Multi-channel notification system for key events
from .notifications import (
    KeyNotifier, KeyEventType, NotificationChannel,
    NotificationPriority, NotificationConfig
)

# Core type definitions for key management
from .types import KeyID, KeyHash, KeySecret, KeyValidationResult

# Conditional imports for external service dependencies
if TYPE_CHECKING:
    from ...monitoring import MetricsClient
    from ...cache import CacheClient
    from ...messaging import MessageBroker

# Public API surface - grouped by functionality for clarity
__all__ = [
    # Key management
    "APIKeyManager",
    
    # Policies
    "KeyType", "KeyPolicy", "ComplianceRequirements",
    "SecurityControls", "ResourceQuota", "TimeWindow",
    "CircuitBreaker",
    
    # Rotation
    "KeyRotationManager", "RotationReason", "RotationConfig",
    
    # Validation
    "KeyValidator", "KeyValidationConfig",
    
    # Notifications
    "KeyNotifier", "KeyEventType", "NotificationChannel",
    "NotificationPriority", "NotificationConfig",
    
    # Types
    "KeyID", "KeyHash", "KeySecret", "KeyValidationResult"
] 