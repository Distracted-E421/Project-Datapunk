from typing import List, Dict, Optional
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
import json
import csv
import io
from .audit import AuditEvent
from ..monitoring import MetricsClient

logger = structlog.get_logger()

@dataclass
class ReportConfig:
    """Configuration for audit report generation."""
    start_date: datetime
    end_date: datetime
    event_types: Optional[List[str]] = None
    services: Optional[List[str]] = None
    actors: Optional[List[str]] = None
    format: str = "json"  # json, csv
    include_metadata: bool = True
    max_events: Optional[int] = None

class AuditReportGenerator:
    """Generates audit reports from event logs."""
    
    def __init__(self,
                 cache_client,
                 metrics: MetricsClient):
        self.cache = cache_client
        self.metrics = metrics
        self.logger = logger.bind(component="audit_reports")
    
    async def generate_report(self,
                            config: ReportConfig) -> bytes:
        """Generate audit report based on configuration."""
        try:
            # Collect events
            events = await self._collect_events(config)
            
            # Filter events
            filtered_events = self._filter_events(events, config)
            
            # Format report
            if config.format == "json":
                return self._format_json(filtered_events, config)
            elif config.format == "csv":
                return self._format_csv(filtered_events, config)
            else:
                raise ValueError(f"Unsupported format: {config.format}")
            
        except Exception as e:
            self.logger.error("report_generation_failed",
                            error=str(e),
                            config=vars(config))
            raise
    
    async def _collect_events(self,
                            config: ReportConfig) -> List[Dict]:
        """Collect audit events from storage."""
        events = []
        pattern = "audit:event:*"
        
        async for key in self.cache.scan_iter(pattern):
            event_data = await self.cache.get(key)
            if event_data:
                event = json.loads(event_data)
                event_time = datetime.fromisoformat(event["timestamp"])
                
                if (event_time >= config.start_date and 
                    event_time <= config.end_date):
                    events.append(event)
                    
                if config.max_events and len(events) >= config.max_events:
                    break
        
        return events
    
    def _filter_events(self,
                      events: List[Dict],
                      config: ReportConfig) -> List[Dict]:
        """Filter events based on configuration."""
        filtered = events
        
        if config.event_types:
            filtered = [
                e for e in filtered
                if e["event_type"] in config.event_types
            ]
            
        if config.services:
            filtered = [
                e for e in filtered
                if e["resource_type"] in config.services
            ]
            
        if config.actors:
            filtered = [
                e for e in filtered
                if e["actor_id"] in config.actors
            ]
            
        return filtered
    
    def _format_json(self,
                    events: List[Dict],
                    config: ReportConfig) -> bytes:
        """Format events as JSON."""
        report = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "start_date": config.start_date.isoformat(),
                "end_date": config.end_date.isoformat(),
                "event_count": len(events)
            },
            "events": events
        }
        
        return json.dumps(report, indent=2).encode('utf-8')
    
    def _format_csv(self,
                   events: List[Dict],
                   config: ReportConfig) -> bytes:
        """Format events as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            "timestamp",
            "event_type",
            "actor_id",
            "resource_type",
            "resource_id",
            "action",
            "status"
        ]
        writer.writerow(headers)
        
        # Write events
        for event in events:
            row = [
                event["timestamp"],
                event["event_type"],
                event["actor_id"],
                event["resource_type"],
                event["resource_id"],
                event["action"],
                event["status"]
            ]
            writer.writerow(row)
        
        return output.getvalue().encode('utf-8') 