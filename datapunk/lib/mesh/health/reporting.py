"""
Health Reporting System

Generates comprehensive health reports for the Datapunk service mesh, supporting
multiple output formats and report types. Designed to provide both human-readable
and machine-parseable health status information.

Key Features:
- Multiple output formats (JSON, HTML, CSV, Markdown, Excel)
- Various report types (summary, detailed, metrics, alerts, trends)
- Configurable retention policies
- Automated cleanup
- Metric tracking
- Visual representations

NOTE: Excel report generation requires significant memory for large datasets.
Consider using CSV format for very large reports or resource-constrained environments.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
from .monitoring import HealthMetrics, MonitoringLevel
from ..discovery.registry import ServiceRegistration
import pandas as pd
import numpy as np
from pathlib import Path
import csv
import io
from jinja2 import Template
import tabulate
import base64
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import PatternFill, Font

class ReportFormat(Enum):
    """
    Supported output formats for health reports.
    
    Format selection impacts:
    - File size
    - Processing time
    - Human readability
    - Machine parseability
    """
    JSON = "json"      # Machine-readable, good for API responses
    HTML = "html"      # Rich formatting, interactive features
    CSV = "csv"        # Lightweight, spreadsheet-compatible
    MARKDOWN = "markdown"  # Human-readable, version control friendly
    EXCEL = "excel"    # Rich formatting, data analysis features

class ReportType(Enum):
    """
    Available health report types.
    
    Each type provides different levels of detail and analysis:
    - SUMMARY: Quick overview of system health
    - DETAILED: In-depth analysis with all metrics
    - METRICS: Raw performance data
    - ALERTS: Security and health incidents
    - TRENDS: Pattern analysis and predictions
    """
    SUMMARY = "summary"
    DETAILED = "detailed"
    METRICS = "metrics"
    ALERTS = "alerts"
    TRENDS = "trends"

@dataclass
class ReportConfig:
    """
    Configuration for health report generation.
    
    Controls report behavior, storage, and cleanup policies.
    Memory usage scales with retention period and report complexity.
    
    TODO: Add support for report compression
    TODO: Implement report archiving strategy
    """
    report_dir: str = "./reports"  # Report storage location
    default_format: ReportFormat = ReportFormat.JSON
    retention_days: int = 30  # Report retention period
    include_metrics: bool = True  # Include performance metrics
    include_alerts: bool = True  # Include alert history
    include_trends: bool = True  # Include trend analysis
    max_trend_points: int = 100  # Max points for trend analysis
    auto_cleanup: bool = True  # Enable automatic report cleanup

class HealthReporter:
    """
    Handles health report generation and formatting.
    
    Coordinates with monitoring system to collect health data and generate
    comprehensive reports in various formats. Implements automatic cleanup
    and metric tracking.
    
    IMPORTANT: Some report formats (especially Excel) can be resource-intensive
    for large datasets. Monitor memory usage when generating complex reports.
    """
    def __init__(
        self,
        config: ReportConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.metrics = metrics_collector
        # Ensure report directory exists
        Path(config.report_dir).mkdir(parents=True, exist_ok=True)

    async def generate_report(
        self,
        report_type: ReportType,
        format: Optional[ReportFormat] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        services: Optional[List[str]] = None
    ) -> Union[str, Dict]:
        """
        Generate health report based on specified parameters.
        
        Handles report generation workflow:
        1. Collect relevant metrics
        2. Generate base report data
        3. Format report
        4. Save report (if configured)
        5. Track metrics
        
        NOTE: Large date ranges or many services may impact performance.
        Consider using pagination or splitting into multiple reports.
        
        Args:
            report_type: Type of report to generate
            format: Output format (defaults to configured default)
            start_time: Report period start
            end_time: Report period end
            services: Specific services to include
            
        Returns:
            Formatted report content
            
        Raises:
            ValueError: For invalid report parameters
            IOError: For report storage issues
        """
        format = format or self.config.default_format
        end_time = end_time or datetime.utcnow()
        start_time = start_time or (end_time - timedelta(hours=24))

        try:
            # Generate appropriate report type
            if report_type == ReportType.SUMMARY:
                report_data = await self._generate_summary_report(services)
            elif report_type == ReportType.DETAILED:
                report_data = await self._generate_detailed_report(services)
            elif report_type == ReportType.METRICS:
                report_data = await self._generate_metrics_report(start_time, end_time, services)
            elif report_type == ReportType.ALERTS:
                report_data = await self._generate_alerts_report(start_time, end_time, services)
            elif report_type == ReportType.TRENDS:
                report_data = await self._generate_trends_report(services)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")

            # Format and save report
            formatted_report = await self._format_report(report_data, format)
            if self.config.report_dir:
                await self._save_report(formatted_report, report_type, format)

            # Track metrics if enabled
            if self.metrics:
                await self.metrics.increment(
                    "health.report.generated",
                    tags={
                        "type": report_type.value,
                        "format": format.value
                    }
                )

            return formatted_report

        except Exception as e:
            # Track generation failures
            if self.metrics:
                await self.metrics.increment(
                    "health.report.error",
                    tags={
                        "type": report_type.value,
                        "error": str(e)
                    }
                )
            raise 