"""
Purpose:
    Provides a comprehensive approval management system for handling authorization policies
    and validation workflows within the Datapunk framework.

Context:
    This module serves as the main entry point for the approval subsystem within the auth policy
    framework. It exposes core components for managing approval workflows, status tracking,
    and validation rules.

Design/Details:
    The module implements a layered approach to approval management:
    - ApprovalManager: Handles the lifecycle of approval requests
    - ApprovalStatus: Tracks the state of approval requests
    - ApprovalLevel: Defines hierarchical approval requirements
    - ApprovalValidator: Enforces validation rules for approvals

Dependencies:
    - MetricsClient: For monitoring approval flows
    - CacheClient: For caching approval states and reducing database load
"""

from typing import TYPE_CHECKING

from .manager import ApprovalManager, ApprovalStatus, ApprovalLevel, ApprovalRequest
from .validation import ApprovalValidator, ApprovalValidationConfig

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient

__all__ = [
    'ApprovalManager',
    'ApprovalStatus',
    'ApprovalLevel',
    'ApprovalRequest',
    'ApprovalValidator',
    'ApprovalValidationConfig'
] 