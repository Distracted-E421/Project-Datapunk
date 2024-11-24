"""
Report template system for audit reports.

This module implements a flexible template engine for generating standardized audit reports
across different security and compliance domains. It uses a composable architecture where
different template types can be mixed and matched based on reporting requirements.

Key features:
- Modular template system with specialized handlers for compliance, security, and metrics
- Configurable sections and formatting options
- Support for custom templates via Jinja2
- Standardized metadata and timestamp handling
- Built-in error handling and logging

Implementation Notes:
- Templates are loaded from the package's templates directory
- All templates use Jinja2 for rendering
- Custom templates must follow the established section structure
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from enum import Enum
import structlog
from datetime import datetime
import json
import yaml
import markdown
import jinja2
from dataclasses import dataclass

from ..types import AuditLevel, ComplianceStandard
from ...core.exceptions import ReportingError

logger = structlog.get_logger()

class TemplateType(Enum):
    """
    Defines the available report template types.
    
    NOTE: When adding new template types, ensure corresponding template files
    are added to the templates directory and update get_template() method.
    """
    BASIC = "basic"           # Simple event listing
    DETAILED = "detailed"     # Detailed analysis
    SUMMARY = "summary"       # High-level overview
    COMPLIANCE = "compliance" # Compliance-focused
    SECURITY = "security"    # Security-focused
    METRICS = "metrics"      # Metrics-focused
    CUSTOM = "custom"        # Custom template

class ReportSection(Enum):
    """
    Standard report sections that can be included in templates.
    
    These sections are designed to align with common audit reporting requirements
    and compliance frameworks. The order here represents the recommended
    presentation order in reports.
    """
    OVERVIEW = "overview"
    SUMMARY = "summary"
    DETAILS = "details"
    METRICS = "metrics"
    GRAPHS = "graphs"
    COMPLIANCE = "compliance"
    RECOMMENDATIONS = "recommendations"
    INCIDENTS = "incidents"
    TRENDS = "trends"
    APPENDIX = "appendix"

@dataclass
class TemplateConfig:
    """
    Configuration settings for report template rendering.
    
    This class controls the presentation and content limits for reports.
    Default values are set to comply with common audit report requirements.
    
    NOTE: graph_format and table_format should align with the output
    system's capabilities (e.g., PDF generator, web display).
    """
    include_sections: List[ReportSection]
    show_timestamps: bool = True
    show_metadata: bool = True
    max_detail_entries: Optional[int] = None
    graph_format: str = "svg"
    table_format: str = "grid"

class ReportTemplate:
    """
    Base template class implementing core rendering logic.
    
    This class provides the foundation for all report templates with common
    functionality for section rendering, metadata handling, and error management.
    
    Implementation Notes:
    - Uses Jinja2 for template rendering
    - Templates are loaded from package resources
    - All derived classes should implement specialized _render_section methods
    """
    
    def __init__(self, config: TemplateConfig):
        self.config = config
        self.logger = logger.bind(component="report_template")
        self.jinja_env = jinja2.Environment(
            loader=jinja2.PackageLoader(__package__, "templates"),
            autoescape=True
        )
    
    @staticmethod
    def get_template(template_type: TemplateType,
                    report_type: str,
                    custom_template: Optional[str] = None) -> 'ReportTemplate':
        """
        Factory method for creating appropriate template instances.
        
        Why Factory Pattern:
        - Encapsulates template instantiation logic
        - Allows for runtime template type selection
        - Maintains consistent configuration across template types
        
        NOTE: When adding new template types, update this method to handle
        the new type and its specific configuration requirements.
        """
        if template_type == TemplateType.COMPLIANCE:
            return ComplianceTemplate(TemplateConfig(
                include_sections=[
                    ReportSection.OVERVIEW,
                    ReportSection.COMPLIANCE,
                    ReportSection.DETAILS,
                    ReportSection.RECOMMENDATIONS
                ]
            ))
        elif template_type == TemplateType.SECURITY:
            return SecurityTemplate(TemplateConfig(
                include_sections=[
                    ReportSection.OVERVIEW,
                    ReportSection.INCIDENTS,
                    ReportSection.METRICS,
                    ReportSection.RECOMMENDATIONS
                ]
            ))
        elif template_type == TemplateType.METRICS:
            return MetricsTemplate(TemplateConfig(
                include_sections=[
                    ReportSection.OVERVIEW,
                    ReportSection.METRICS,
                    ReportSection.GRAPHS,
                    ReportSection.TRENDS
                ],
                graph_format="svg"
            ))
        elif template_type == TemplateType.CUSTOM and custom_template:
            return CustomTemplate(
                TemplateConfig(include_sections=[]),
                custom_template
            )
        else:
            return BasicTemplate(TemplateConfig(
                include_sections=[
                    ReportSection.OVERVIEW,
                    ReportSection.SUMMARY,
                    ReportSection.DETAILS
                ]
            ))
    
    def render(self,
              sections: Dict[str, Any],
              config: Any,
              metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Render report sections."""
        try:
            rendered_sections = {}
            
            for section in self.config.include_sections:
                if section.value in sections:
                    rendered_sections[section.value] = self._render_section(
                        section,
                        sections[section.value],
                        config
                    )
            
            return {
                "metadata": self._render_metadata(metadata),
                "sections": rendered_sections
            }
            
        except Exception as e:
            self.logger.error("template_rendering_failed",
                            error=str(e))
            raise ReportingError(f"Failed to render template: {str(e)}")
    
    def _render_section(self,
                       section: ReportSection,
                       data: Any,
                       config: Any) -> str:
        """Render a single section."""
        template = self.jinja_env.get_template(f"{section.value}.j2")
        return template.render(
            data=data,
            config=config,
            show_timestamps=self.config.show_timestamps,
            show_metadata=self.config.show_metadata
        )
    
    def _render_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Render report metadata."""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "template_type": self.__class__.__name__,
            **metadata
        }

class ComplianceTemplate(ReportTemplate):
    """
    Specialized template for compliance reporting.
    
    Handles structured presentation of compliance requirements, violations,
    and recommendations. Designed to align with major compliance frameworks
    like SOC2, ISO27001, and HIPAA.
    
    FUTURE: Consider adding support for framework-specific formatting rules
    and automatic mapping of controls to requirements.
    """
    
    def _render_section(self,
                       section: ReportSection,
                       data: Any,
                       config: Any) -> str:
        """Render compliance-specific sections."""
        if section == ReportSection.COMPLIANCE:
            return self._render_compliance_matrix(data)
        elif section == ReportSection.RECOMMENDATIONS:
            return self._render_compliance_recommendations(data)
        return super()._render_section(section, data, config)
    
    def _render_compliance_matrix(self, data: Dict) -> str:
        """
        Renders a compliance requirements traceability matrix.
        
        The matrix maps requirements to implementation status and evidence.
        Assumes data contains 'requirements', 'status', and 'evidence' keys.
        """
        template = self.jinja_env.get_template("compliance_matrix.j2")
        return template.render(data=data)
    
    def _render_compliance_recommendations(self, data: List) -> str:
        """Render compliance recommendations."""
        template = self.jinja_env.get_template("compliance_recommendations.j2")
        return template.render(recommendations=data)

class SecurityTemplate(ReportTemplate):
    """
    Specialized template for security incident and assessment reporting.
    
    Focuses on presenting security events, incident analysis, and remediation
    recommendations in a format suitable for both technical and non-technical
    stakeholders.
    
    TODO: Add support for severity-based formatting and automatic incident
    categorization based on industry standards (e.g., CVSS scores).
    """
    
    def _render_section(self,
                       section: ReportSection,
                       data: Any,
                       config: Any) -> str:
        """Render security-specific sections."""
        if section == ReportSection.INCIDENTS:
            return self._render_security_incidents(data)
        elif section == ReportSection.RECOMMENDATIONS:
            return self._render_security_recommendations(data)
        return super()._render_section(section, data, config)
    
    def _render_security_incidents(self, incidents: List) -> str:
        """Render security incidents."""
        template = self.jinja_env.get_template("security_incidents.j2")
        return template.render(incidents=incidents)

class MetricsTemplate(ReportTemplate):
    """
    Specialized template for security and compliance metrics visualization.
    
    Provides formatted presentation of key security metrics, trends, and
    performance indicators. Supports various graph formats for different
    output requirements.
    
    NOTE: The graph_format setting in config must match supported formats
    in the visualization backend (currently supports 'svg' only).
    """
    
    def _render_section(self,
                       section: ReportSection,
                       data: Any,
                       config: Any) -> str:
        """Render metrics-specific sections."""
        if section == ReportSection.METRICS:
            return self._render_metrics_dashboard(data)
        elif section == ReportSection.GRAPHS:
            return self._render_metric_graphs(data)
        elif section == ReportSection.TRENDS:
            return self._render_trend_analysis(data)
        return super()._render_section(section, data, config)
    
    def _render_metrics_dashboard(self, metrics: Dict) -> str:
        """Render metrics dashboard."""
        template = self.jinja_env.get_template("metrics_dashboard.j2")
        return template.render(
            metrics=metrics,
            graph_format=self.config.graph_format
        )

class CustomTemplate(ReportTemplate):
    """
    Allows for user-defined report templates while maintaining consistent
    metadata handling and error management.
    
    SECURITY NOTE: Custom templates should be validated before use to prevent
    template injection attacks. Consider implementing template sanitization.
    
    TODO: Add template validation and sanitization logic
    """
    
    def __init__(self,
                 config: TemplateConfig,
                 template_string: str):
        super().__init__(config)
        self.template = self.jinja_env.from_string(template_string)
    
    def render(self,
              sections: Dict[str, Any],
              config: Any,
              metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Render using custom template."""
        try:
            return {
                "content": self.template.render(
                    sections=sections,
                    config=config,
                    metadata=metadata
                ),
                "metadata": self._render_metadata(metadata)
            }
        except Exception as e:
            self.logger.error("custom_template_rendering_failed",
                            error=str(e))
            raise ReportingError(f"Failed to render custom template: {str(e)}") 