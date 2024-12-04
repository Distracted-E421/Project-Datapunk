"""
Policy Management and Enforcement Module

Purpose:
    Provides a comprehensive framework for managing, enforcing, and validating security 
    policies across the Datapunk application.

Context:
    This module serves as the central hub for all policy-related functionality, including
    approval workflows, enforcement rules, and rollback mechanisms.

Design:
    The module is structured into three main components:
    1. Policy Types & Core Functionality
    2. Approval Management
    3. Policy Enforcement
    4. Rollback Handling
"""

from typing import TYPE_CHECKING

# Core policy types and validation components
from .types import (
    PolicyType, PolicyStatus, RiskLevel,
    PolicyRule, Policy, PolicyValidationResult,
    PolicyEvaluationResult
)

# Approval workflow management components
from .approval.manager import (
    ApprovalManager, ApprovalStatus, ApprovalLevel,
    ApprovalRequest, ApprovalValidationConfig
)

# Policy enforcement and rule processing
from .enforcement.middleware import PolicyEnforcementMiddleware
from .enforcement.rules import (
    RuleEngine, RuleType, EnforcementRule,
    TimeBasedRule, RateLimitRule
)

# Rollback functionality for policy changes
from .rollback.manager import RollbackManager, RollbackPoint

# Optional dependencies for metrics and caching
if TYPE_CHECKING:
    from ...monitoring import MetricsClient
    from ...cache import CacheClient

# Public API exports
__all__ = [
    # Core policy types and structures
    "PolicyType", "PolicyStatus", "RiskLevel",
    "PolicyRule", "Policy", "PolicyValidationResult",
    "PolicyEvaluationResult",
    
    # Approval workflow components
    "ApprovalManager", "ApprovalStatus", "ApprovalLevel",
    "ApprovalRequest", "ApprovalValidationConfig",
    
    # Policy enforcement mechanisms
    "PolicyEnforcementMiddleware", "RuleEngine", "RuleType",
    "EnforcementRule", "TimeBasedRule", "RateLimitRule",
    
    # Rollback functionality
    "RollbackManager", "RollbackPoint"
] 