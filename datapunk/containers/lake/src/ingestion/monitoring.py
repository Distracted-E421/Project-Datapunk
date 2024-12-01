from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass, field
from collections import defaultdict
import json
from enum import Enum

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics that can be collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class MetricValue:
    """Value container for metrics with metadata"""
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)

class MetricCollector:
    """Collects and manages metrics"""
    
    def __init__(self):
        self._metrics: Dict[str, Dict[MetricType, List[MetricValue]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._retention_period = timedelta(hours=24)
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the metric collector"""
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
    async def stop(self):
        """Stop the metric collector"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a metric value"""
        metric = MetricValue(
            value=value,
            labels=labels or {}
        )
        self._metrics[name][metric_type].append(metric)
        
    async def get_metrics(
        self,
        name: Optional[str] = None,
        metric_type: Optional[MetricType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Dict[str, List[MetricValue]]]:
        """Retrieve metrics based on filters"""
        result = {}
        
        metrics = {name: self._metrics[name]} if name else self._metrics
        for metric_name, type_values in metrics.items():
            result[metric_name] = {}
            types = {metric_type: type_values[metric_type]} if metric_type else type_values
            
            for m_type, values in types.items():
                filtered_values = [
                    v for v in values
                    if (not start_time or v.timestamp >= start_time) and
                       (not end_time or v.timestamp <= end_time)
                ]
                if filtered_values:
                    result[metric_name][m_type.value] = filtered_values
                    
        return result
        
    async def _periodic_cleanup(self):
        """Periodically clean up old metrics"""
        while True:
            try:
                await asyncio.sleep(3600)  # Cleanup every hour
                await self._cleanup_old_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metric cleanup: {str(e)}")
                
    async def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff = datetime.utcnow() - self._retention_period
        for metric_name in self._metrics:
            for metric_type in self._metrics[metric_name]:
                self._metrics[metric_name][metric_type] = [
                    m for m in self._metrics[metric_name][metric_type]
                    if m.timestamp > cutoff
                ]

class HandlerMetrics:
    """Metrics collection for data handlers"""
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        
    async def record_processing_time(self, handler_type: str, duration: float):
        """Record processing time for a handler"""
        await self.collector.record_metric(
            f"{handler_type}_processing_time",
            duration,
            MetricType.HISTOGRAM,
            {"handler": handler_type}
        )
        
    async def record_data_size(self, handler_type: str, size: int):
        """Record size of processed data"""
        await self.collector.record_metric(
            f"{handler_type}_data_size",
            size,
            MetricType.HISTOGRAM,
            {"handler": handler_type}
        )
        
    async def record_error(self, handler_type: str, error_type: str):
        """Record processing errors"""
        await self.collector.record_metric(
            f"{handler_type}_errors",
            1,
            MetricType.COUNTER,
            {"handler": handler_type, "error": error_type}
        )
        
    async def record_success(self, handler_type: str):
        """Record successful processing"""
        await self.collector.record_metric(
            f"{handler_type}_success",
            1,
            MetricType.COUNTER,
            {"handler": handler_type}
        )
        
    async def record_queue_size(self, handler_type: str, size: int):
        """Record current queue size"""
        await self.collector.record_metric(
            f"{handler_type}_queue_size",
            size,
            MetricType.GAUGE,
            {"handler": handler_type}
        )

class MetricsExporter:
    """Exports metrics in various formats"""
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        
    async def export_json(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> str:
        """Export metrics as JSON"""
        metrics = await self.collector.get_metrics(
            start_time=start_time,
            end_time=end_time
        )
        
        # Convert to serializable format
        serializable = {}
        for metric_name, type_values in metrics.items():
            serializable[metric_name] = {}
            for type_name, values in type_values.items():
                serializable[metric_name][type_name] = [
                    {
                        "value": v.value,
                        "timestamp": v.timestamp.isoformat(),
                        "labels": v.labels
                    }
                    for v in values
                ]
                
        return json.dumps(serializable, indent=2)
        
    async def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        metrics = await self.collector.get_metrics()
        output = []
        
        for metric_name, type_values in metrics.items():
            for type_name, values in type_values.items():
                # Add metric help and type
                output.append(f"# HELP {metric_name} {type_name}")
                output.append(f"# TYPE {metric_name} {type_name}")
                
                # Add metric values
                for value in values:
                    if value.labels:
                        labels = ",".join(
                            f'{k}="{v}"'
                            for k, v in value.labels.items()
                        )
                        output.append(
                            f'{metric_name}{{{labels}}} {value.value}'
                        )
                    else:
                        output.append(f"{metric_name} {value.value}")
                        
        return "\n".join(output) 