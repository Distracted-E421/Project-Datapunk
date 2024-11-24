from typing import List, Dict, Optional
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
import pandas as pd
import matplotlib.pyplot as plt
import io
from .audit_reports import ReportConfig

logger = structlog.get_logger()

@dataclass
class ComplianceReportConfig(ReportConfig):
    """Configuration for compliance reports."""
    standards: List[str]
    include_pii_analysis: bool = True
    include_violations: bool = True
    risk_assessment: bool = True

@dataclass
class SecurityReportConfig(ReportConfig):
    """Configuration for security reports."""
    include_failed_attempts: bool = True
    include_suspicious_activity: bool = True
    severity_threshold: str = "warning"

class ExtendedReportGenerator:
    """Generates specialized audit reports."""
    
    def __init__(self, base_generator):
        self.base = base_generator
        self.logger = logger.bind(component="extended_reports")
    
    async def generate_compliance_report(self,
                                      config: ComplianceReportConfig) -> bytes:
        """Generate compliance-focused report."""
        try:
            # Get base events
            events = await self.base._collect_events(config)
            
            # Add compliance analysis
            report_data = {
                "metadata": {
                    "report_type": "compliance",
                    "standards": config.standards,
                    "generated_at": datetime.utcnow().isoformat(),
                    "period": {
                        "start": config.start_date.isoformat(),
                        "end": config.end_date.isoformat()
                    }
                },
                "summary": await self._analyze_compliance(events, config),
                "violations": await self._find_violations(events) if config.include_violations else [],
                "risk_assessment": await self._assess_risk(events) if config.risk_assessment else None,
                "events": events
            }
            
            return self._format_report(report_data, config.format)
            
        except Exception as e:
            self.logger.error("compliance_report_generation_failed",
                            error=str(e))
            raise
    
    async def generate_security_report(self,
                                     config: SecurityReportConfig) -> bytes:
        """Generate security-focused report."""
        try:
            events = await self.base._collect_events(config)
            
            report_data = {
                "metadata": {
                    "report_type": "security",
                    "generated_at": datetime.utcnow().isoformat(),
                    "period": {
                        "start": config.start_date.isoformat(),
                        "end": config.end_date.isoformat()
                    }
                },
                "summary": await self._analyze_security(events, config),
                "failed_attempts": await self._analyze_failures(events) if config.include_failed_attempts else [],
                "suspicious_activity": await self._detect_suspicious(events) if config.include_suspicious_activity else [],
                "events": events
            }
            
            return self._format_report(report_data, config.format)
            
        except Exception as e:
            self.logger.error("security_report_generation_failed",
                            error=str(e))
            raise
    
    async def generate_visual_report(self,
                                   events: List[Dict],
                                   report_type: str) -> bytes:
        """Generate visual report with charts and graphs."""
        try:
            df = pd.DataFrame(events)
            
            # Create visualization
            plt.figure(figsize=(12, 8))
            
            if report_type == "activity":
                self._create_activity_chart(df)
            elif report_type == "security":
                self._create_security_chart(df)
            elif report_type == "compliance":
                self._create_compliance_chart(df)
            
            # Save plot to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            return buf.getvalue()
            
        except Exception as e:
            self.logger.error("visual_report_generation_failed",
                            error=str(e))
            raise
    
    def _create_activity_chart(self, df: pd.DataFrame) -> None:
        """Create activity visualization."""
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        activity = df.groupby([pd.Grouper(key='timestamp', freq='1H'), 'action']).size().unstack()
        activity.plot(kind='area', stacked=True)
        plt.title('Activity Over Time')
        plt.xlabel('Time')
        plt.ylabel('Number of Events')
    
    def _create_security_chart(self, df: pd.DataFrame) -> None:
        """Create security visualization."""
        security_events = df[df['event_type'].str.contains('security')].groupby('status').size()
        security_events.plot(kind='pie', autopct='%1.1f%%')
        plt.title('Security Event Distribution')
    
    def _create_compliance_chart(self, df: pd.DataFrame) -> None:
        """Create compliance visualization."""
        compliance = df.groupby(['compliance.standards', 'status']).size().unstack()
        compliance.plot(kind='bar', stacked=True)
        plt.title('Compliance Status by Standard')
        plt.xlabel('Compliance Standard')
        plt.ylabel('Number of Events') 