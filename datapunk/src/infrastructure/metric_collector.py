from enum import Enum
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
import statistics
import logging
from dataclasses import dataclass
from collections import defaultdict
import asyncio
import json

logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AggregationType(Enum):
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    P50 = "p50"
    P90 = "p90"
    P95 = "p95"
    P99 = "p99"

@dataclass
class MetricValue:
    value: Union[int, float]
    timestamp: datetime
    labels: Optional[Dict[str, str]] = None

@dataclass
class MetricDefinition:
    name: str
    type: MetricType
    description: str
    unit: str
    aggregations: List[AggregationType]
    retention_period: timedelta
    labels: Optional[List[str]] = None

class MetricAggregator:
    """Handles metric aggregation over time windows."""
    
    def __init__(self, window_size: timedelta):
        self.window_size = window_size
        self.values: List[MetricValue] = []
    
    def add_value(self, value: MetricValue) -> None:
        """Add a new value to the aggregator."""
        self.values.append(value)
        self._cleanup_old_values()
    
    def _cleanup_old_values(self) -> None:
        """Remove values older than the window size."""
        cutoff = datetime.now() - self.window_size
        self.values = [v for v in self.values if v.timestamp > cutoff]
    
    def get_aggregation(self, agg_type: AggregationType) -> Optional[float]:
        """Calculate the specified aggregation over current values."""
        if not self.values:
            return None
        
        raw_values = [v.value for v in self.values]
        
        if agg_type == AggregationType.SUM:
            return sum(raw_values)
        elif agg_type == AggregationType.AVG:
            return statistics.mean(raw_values)
        elif agg_type == AggregationType.MIN:
            return min(raw_values)
        elif agg_type == AggregationType.MAX:
            return max(raw_values)
        elif agg_type == AggregationType.COUNT:
            return len(raw_values)
        elif agg_type == AggregationType.P50:
            return statistics.median(raw_values)
        elif agg_type == AggregationType.P90:
            return statistics.quantiles(raw_values, n=10)[-1]
        elif agg_type == AggregationType.P95:
            return statistics.quantiles(raw_values, n=20)[-1]
        elif agg_type == AggregationType.P99:
            return statistics.quantiles(raw_values, n=100)[-1]
        else:
            raise ValueError(f"Unsupported aggregation type: {agg_type}")

class MetricStorage:
    """Handles persistent storage of metrics."""
    
    def __init__(self, retention_period: timedelta):
        self.retention_period = retention_period
        self.metrics: Dict[str, List[MetricValue]] = defaultdict(list)
    
    def store_metric(self, name: str, value: MetricValue) -> None:
        """Store a metric value."""
        self.metrics[name].append(value)
        self._cleanup_old_metrics(name)
    
    def _cleanup_old_metrics(self, name: str) -> None:
        """Remove metrics older than the retention period."""
        cutoff = datetime.now() - self.retention_period
        self.metrics[name] = [
            v for v in self.metrics[name] if v.timestamp > cutoff
        ]
    
    def get_metrics(self, name: str, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   labels: Optional[Dict[str, str]] = None) -> List[MetricValue]:
        """Retrieve metrics with optional filtering."""
        metrics = self.metrics.get(name, [])
        
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        if labels:
            metrics = [
                m for m in metrics 
                if m.labels and all(m.labels.get(k) == v for k, v in labels.items())
            ]
        
        return metrics

class MetricCollector:
    """Main metric collection and management system."""
    
    def __init__(self):
        self.definitions: Dict[str, MetricDefinition] = {}
        self.aggregators: Dict[str, Dict[str, MetricAggregator]] = defaultdict(dict)
        self.storage: Dict[str, MetricStorage] = {}
        self._running = False
        self._aggregation_task: Optional[asyncio.Task] = None
    
    def register_metric(self, definition: MetricDefinition) -> None:
        """Register a new metric definition."""
        if definition.name in self.definitions:
            raise ValueError(f"Metric '{definition.name}' already registered")
        
        self.definitions[definition.name] = definition
        self.storage[definition.name] = MetricStorage(definition.retention_period)
        
        # Create aggregators for different time windows
        self.aggregators[definition.name] = {
            "1min": MetricAggregator(timedelta(minutes=1)),
            "5min": MetricAggregator(timedelta(minutes=5)),
            "15min": MetricAggregator(timedelta(minutes=15)),
            "1hour": MetricAggregator(timedelta(hours=1)),
            "1day": MetricAggregator(timedelta(days=Metric1))
        }
        
        logger.info(f"Registered metric: {definition.name}")
    
    def record_metric(self, name: str, value: Union[int, float], 
                     labels: Optional[Dict[str, str]] = None) -> None:
        """Record a new metric value."""
        if name not in self.definitions:
            raise ValueError(f"Metric '{name}' not registered")
        
        definition = self.definitions[name]
        
        # Validate labels
        if definition.labels:
            if not labels:
                raise ValueError(f"Labels required for metric '{name}'")
            if not all(label in labels for label in definition.labels):
                raise ValueError(f"Missing required labels for metric '{name}'")
        
        metric_value = MetricValue(
            value=value,
            timestamp=datetime.now(),
            labels=labels
        )
        
        # Update aggregators
        for aggregator in self.aggregators[name].values():
            aggregator.add_value(metric_value)
        
        # Store the raw value
        self.storage[name].store_metric(name, metric_value)
    
    def get_metric_aggregation(self, name: str, window: str,
                             aggregation: AggregationType) -> Optional[float]:
        """Get an aggregated metric value."""
        if name not in self.definitions:
            raise ValueError(f"Metric '{name}' not registered")
        
        if window not in self.aggregators[name]:
            raise ValueError(f"Invalid window size: {window}")
        
        definition = self.definitions[name]
        if aggregation not in definition.aggregations:
            raise ValueError(
                f"Aggregation {aggregation} not supported for metric '{name}'"
            )
        
        return self.aggregators[name][window].get_aggregation(aggregation)
    
    def get_metric_values(self, name: str,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         labels: Optional[Dict[str, str]] = None) -> List[MetricValue]:
        """Get raw metric values with optional filtering."""
        if name not in self.definitions:
            raise ValueError(f"Metric '{name}' not registered")
        
        return self.storage[name].get_metrics(name, start_time, end_time, labels)
    
    def get_metric_definition(self, name: str) -> Optional[MetricDefinition]:
        """Get the definition of a metric."""
        return self.definitions.get(name)
    
    def list_metrics(self) -> List[str]:
        """List all registered metric names."""
        return list(self.definitions.keys())
    
    def export_metrics(self, format: str = "json") -> str:
        """Export current metric values in the specified format."""
        if format.lower() != "json":
            raise ValueError("Only JSON format is currently supported")
        
        export_data = {}
        for name, definition in self.definitions.items():
            metric_data = {
                "type": definition.type.value,
                "description": definition.description,
                "unit": definition.unit,
                "values": []
            }
            
            # Add current aggregations
            for window, aggregator in self.aggregators[name].items():
                window_data = {"window": window, "aggregations": {}}
                for agg_type in definition.aggregations:
                    value = aggregator.get_aggregation(agg_type)
                    if value is not None:
                        window_data["aggregations"][agg_type.value] = value
                metric_data["values"].append(window_data)
            
            export_data[name] = metric_data
        
        return json.dumps(export_data, default=str)
    
    async def start(self) -> None:
        """Start the metric collector."""
        if self._running:
            return
        
        self._running = True
        self._aggregation_task = asyncio.create_task(self._run_aggregation())
    
    async def stop(self) -> None:
        """Stop the metric collector."""
        self._running = False
        
        if self._aggregation_task:
            self._aggregation_task.cancel()
            try:
                await self._aggregation_task
            except asyncio.CancelledError:
                pass
            self._aggregation_task = None
    
    async def _run_aggregation(self) -> None:
        """Periodically run metric aggregation."""
        while self._running:
            try:
                # Trigger cleanup of old values in all aggregators
                for metric_aggregators in self.aggregators.values():
                    for aggregator in metric_aggregators.values():
                        aggregator._cleanup_old_values()
                
                # Cleanup old stored metrics
                for storage in self.storage.values():
                    for name in list(storage.metrics.keys()):
                        storage._cleanup_old_metrics(name)
            
            except Exception as e:
                logger.error(f"Error during metric aggregation: {e}")
            
            await asyncio.sleep(60)  # Run cleanup every minute 