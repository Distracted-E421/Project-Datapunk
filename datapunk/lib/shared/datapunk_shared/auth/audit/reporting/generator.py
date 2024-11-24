"""
Audit report generation system.

This module handles the generation of audit reports including:
- Compliance reports
- Security incident reports
- Access pattern reports
- Policy change reports
- Key usage reports
"""

from typing import Dict, List, Optional, TYPE_CHECKING, Any
import structlog
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from .templates import ReportTemplate, TemplateType
from ..types import AuditLevel, ComplianceStandard
from ...core.exceptions import ReportingError

if TYPE_CHECKING:
    from ....monitoring import MetricsClient
    from ....cache import CacheClient

logger = structlog.get_logger()

class ReportFormat(Enum):
    """Supported report formats."""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    CSV = "csv"
    MARKDOWN = "markdown"

class ReportType(Enum):
    """Types of audit reports."""
    COMPLIANCE = "compliance"
    SECURITY = "security"
    ACCESS = "access"
    POLICY = "policy"
    KEY_USAGE = "key_usage"
    INCIDENT = "incident"

@dataclass
class ReportConfig:
    """Configuration for report generation."""
    format: ReportFormat
    template_type: TemplateType
    include_metrics: bool = True
    include_graphs: bool = True
    max_entries: Optional[int] = None
    compliance_standards: Optional[List[ComplianceStandard]] = None
    audit_level: AuditLevel = AuditLevel.STANDARD

class ReportGenerator:
    """Generates audit reports from events."""
    
    def __init__(self,
                 cache_client: 'CacheClient',
                 metrics: 'MetricsClient'):
        self.cache = cache_client
        self.metrics = metrics
        self.logger = logger.bind(component="report_generator")
    
    async def generate_report(self,
                            report_type: ReportType,
                            start_time: datetime,
                            end_time: datetime,
                            config: ReportConfig,
                            filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate an audit report."""
        try:
            # Get events for time period
            events = await self._get_events(
                report_type,
                start_time,
                end_time,
                filters
            )
            
            # Apply filters
            if filters:
                events = self._filter_events(events, filters)
            
            # Get template
            template = ReportTemplate.get_template(
                config.template_type,
                report_type
            )
            
            # Generate report sections
            sections = {
                "summary": await self._generate_summary(events, report_type),
                "details": await self._generate_details(events, config),
                "metrics": await self._generate_metrics(report_type, start_time, end_time)
                if config.include_metrics else None,
                "graphs": await self._generate_graphs(events)
                if config.include_graphs else None,
                "compliance": await self._generate_compliance(events, config)
                if config.compliance_standards else None
            }
            
            # Apply template
            report = template.render(
                sections=sections,
                config=config,
                metadata={
                    "generated_at": datetime.utcnow().isoformat(),
                    "report_type": report_type.value,
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat()
                    }
                }
            )
            
            # Format report
            formatted_report = await self._format_report(
                report,
                config.format
            )
            
            # Update metrics
            self.metrics.increment(
                "reports_generated",
                {
                    "type": report_type.value,
                    "format": config.format.value
                }
            )
            
            return formatted_report
            
        except Exception as e:
            self.logger.error("report_generation_failed",
                            error=str(e))
            raise ReportingError(f"Failed to generate report: {str(e)}")
    
    async def _get_events(self,
                         report_type: ReportType,
                         start_time: datetime,
                         end_time: datetime,
                         filters: Optional[Dict]) -> List[Dict]:
        """Get events for report period."""
        try:
            # Get event keys for time range
            pattern = f"audit:events:{report_type.value}:*"
            event_keys = await self.cache.scan(pattern)
            
            events = []
            for key in event_keys:
                event = await self.cache.get(key)
                if event:
                    event_time = datetime.fromisoformat(event["timestamp"])
                    if start_time <= event_time <= end_time:
                        events.append(event)
            
            return events
            
        except Exception as e:
            self.logger.error("event_fetch_failed",
                            error=str(e))
            raise
    
    def _filter_events(self,
                      events: List[Dict],
                      filters: Dict) -> List[Dict]:
        """Apply filters to events."""
        filtered_events = events
        
        for field, value in filters.items():
            if isinstance(value, (str, int, bool)):
                filtered_events = [
                    e for e in filtered_events
                    if e.get(field) == value
                ]
            elif isinstance(value, list):
                filtered_events = [
                    e for e in filtered_events
                    if e.get(field) in value
                ]
            elif isinstance(value, dict):
                # Handle nested filters
                filtered_events = [
                    e for e in filtered_events
                    if all(
                        e.get(k, {}).get(sk) == sv
                        for k, v in value.items()
                        for sk, sv in v.items()
                    )
                ]
        
        return filtered_events
    
    async def _generate_summary(self,
                              events: List[Dict],
                              report_type: ReportType) -> Dict[str, Any]:
        """Generate report summary."""
        return {
            "total_events": len(events),
            "event_types": self._count_field_values(events, "event_type"),
            "status_counts": self._count_field_values(events, "status"),
            "top_users": self._get_top_values(events, "user_id", 5),
            "top_resources": self._get_top_values(events, "resource_id", 5)
        }
    
    async def _generate_details(self,
                              events: List[Dict],
                              config: ReportConfig) -> List[Dict]:
        """Generate detailed event listings."""
        # Limit number of events if configured
        if config.max_entries:
            events = events[:config.max_entries]
        
        # Filter fields based on audit level
        return [
            self._filter_event_fields(event, config.audit_level)
            for event in events
        ]
    
    async def _generate_metrics(self,
                              report_type: ReportType,
                              start_time: datetime,
                              end_time: datetime) -> Dict[str, Any]:
        """Generate metrics for report period."""
        metrics = {}
        
        # Get relevant metrics based on report type
        if report_type == ReportType.ACCESS:
            metrics.update(await self._get_access_metrics(start_time, end_time))
        elif report_type == ReportType.SECURITY:
            metrics.update(await self._get_security_metrics(start_time, end_time))
        
        return metrics
    
    async def _generate_graphs(self,
                             events: List[Dict]) -> Dict[str, Any]:
        """Generate graph data for visualization."""
        # Implementation would generate graph data
        # This is a placeholder
        return {}
    
    async def _generate_compliance(self,
                                 events: List[Dict],
                                 config: ReportConfig) -> Dict[str, Any]:
        """Generate compliance section of report."""
        compliance_data = {}
        
        for standard in config.compliance_standards:
            compliance_data[standard.value] = {
                "compliant": True,  # Placeholder
                "violations": [],   # Placeholder
                "recommendations": []  # Placeholder
            }
        
        return compliance_data
    
    async def _format_report(self,
                           report: Dict,
                           format: ReportFormat) -> Any:
        """Format report in specified format."""
        if format == ReportFormat.JSON:
            return json.dumps(report, indent=2)
        elif format == ReportFormat.HTML:
            return self._format_html(report)
        elif format == ReportFormat.PDF:
            return await self._format_pdf(report)
        elif format == ReportFormat.CSV:
            return self._format_csv(report)
        elif format == ReportFormat.MARKDOWN:
            return self._format_markdown(report)
        else:
            raise ReportingError(f"Unsupported format: {format}")
    
    def _count_field_values(self,
                          events: List[Dict],
                          field: str) -> Dict[str, int]:
        """Count occurrences of field values."""
        counts = {}
        for event in events:
            value = event.get(field)
            if value:
                counts[value] = counts.get(value, 0) + 1
        return counts
    
    def _get_top_values(self,
                       events: List[Dict],
                       field: str,
                       limit: int) -> Dict[str, int]:
        """Get top N values for a field."""
        counts = self._count_field_values(events, field)
        return dict(
            sorted(
                counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
        )
    
    def _filter_event_fields(self,
                           event: Dict,
                           audit_level: AuditLevel) -> Dict:
        """Filter event fields based on audit level."""
        if audit_level == AuditLevel.MINIMAL:
            return {
                k: v for k, v in event.items()
                if k in {"event_id", "event_type", "timestamp", "status"}
            }
        elif audit_level == AuditLevel.STANDARD:
            return {
                k: v for k, v in event.items()
                if not k.startswith("internal_")
            }
        return event  # Return all fields for DETAILED level 