# datapunk/lib/shared/datapunk_shared/auth/audit/reporting/__init__.py

"""
Audit Reporting Module
-------------------

Provides report generation and template management for audit system.
"""

from .generator import (
    ReportGenerator,
    ReportFormat,
    ReportConfig,
    ReportOptions
)

from .templates import (
    TemplateManager,
    TemplateType,
    TemplateContext,
    TemplateData
)

from .template_validator import (
    TemplateValidator,
    ValidationResult,
    ValidationError
)

from .template_cache import (
    TemplateCache,
    CacheConfig,
    CacheEntry
)

from .template_cache_utils import (
    CacheUtils,
    CacheStrategy,
    CacheMetrics
)

from .audit_reports_extended import (
    ExtendedReportGenerator,
    ExtendedReportFormat,
    ExtendedTemplateManager
)

__all__ = [
    # Generator
    'ReportGenerator',
    'ReportFormat',
    'ReportConfig',
    'ReportOptions',
    
    # Templates
    'TemplateManager',
    'TemplateType',
    'TemplateContext',
    'TemplateData',
    
    # Validator
    'TemplateValidator',
    'ValidationResult',
    'ValidationError',
    
    # Cache
    'TemplateCache',
    'CacheConfig',
    'CacheEntry',
    
    # Cache Utils
    'CacheUtils',
    'CacheStrategy',
    'CacheMetrics',
    
    # Extended Reports
    'ExtendedReportGenerator',
    'ExtendedReportFormat',
    'ExtendedTemplateManager'
]