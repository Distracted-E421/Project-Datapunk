"""
Nexus Authentication and Authorization Module

This module provides a comprehensive suite of authentication, authorization, and security services
for the Nexus platform. It includes OAuth2 support, session management, access control, password
management, audit logging, and rate limiting capabilities.
"""

from .nexus_auth_manager import NexusAuthManager
from .nexus_authorization import NexusAuthorization
from .service_auth import ServiceAuth
from .oauth2_manager import OAuth2Manager
from .nexus_session_manager import NexusSessionManager
from .nexus_access_control import NexusAccessControl
from .nexus_password_manager import NexusPasswordManager
from .nexus_audit_logger import NexusAuditLogger
from .nexus_auth_rate_limiter import NexusAuthRateLimiter
from .security_analyzer import SecurityAnalyzer

__all__ = [
    'NexusAuthManager',
    'NexusAuthorization',
    'ServiceAuth',
    'OAuth2Manager',
    'NexusSessionManager',
    'NexusAccessControl',
    'NexusPasswordManager',
    'NexusAuditLogger',
    'NexusAuthRateLimiter',
    'SecurityAnalyzer',
]

# Version information
__version__ = '1.0.0'
__author__ = 'DataPunk Development Team'
