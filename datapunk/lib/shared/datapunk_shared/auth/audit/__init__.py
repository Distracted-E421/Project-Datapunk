"""
Audit logging and compliance tracking module for DataPunk.

This module provides a comprehensive framework for:
- Audit logging with configurable severity levels
- Compliance tracking against various security standards
- Automated report generation for audit and compliance data
- Customizable reporting templates and formats

The module is designed to support enterprise-level security and compliance 
requirements while maintaining flexibility for different regulatory frameworks.
"""

from typing import TYPE_CHECKING

# Core audit types for event tracking and context management
from .types import (
    AuditLevel, ComplianceStandard, AuditEvent,
    AuditContext, AuditResult
)

# Compliance framework components supporting various security standards
# (e.g., SOC2, HIPAA, GDPR, etc.)
from .compliance.standards import (
    ComplianceStandards, ComplianceLevel,
    DataClassification, SecurityControl,
    ComplianceRequirement
)

# Report generation utilities for creating audit and compliance documentation
from .reporting.generator import (
    ReportGenerator, ReportFormat, ReportType,
    ReportConfig
)

# Customizable template system for standardized report layouts
from .reporting.templates import (
    ReportTemplate, TemplateType, ReportSection,
    TemplateConfig
)

# Optional dependencies for metrics and caching support
# NOTE: These are only used for type checking and should be configured
# at runtime based on application needs
if TYPE_CHECKING:
    from ...monitoring import MetricsClient
    from ...cache import CacheClient

# Public API exports
# Organized by functional area to maintain clear boundaries between
# audit types, compliance tools, and reporting capabilities
__all__ = [
    # Types
    "AuditLevel", "ComplianceStandard", "AuditEvent",
    "AuditContext", "AuditResult",
    
    # Compliance
    "ComplianceStandards", "ComplianceLevel",
    "DataClassification", "SecurityControl",
    "ComplianceRequirement",
    
    # Reporting
    "ReportGenerator", "ReportFormat", "ReportType",
    "ReportConfig", "ReportTemplate", "TemplateType",
    "ReportSection", "TemplateConfig"
] 