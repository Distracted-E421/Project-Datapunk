from typing import Optional, Dict, Any, List, Union, Set
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import statistics
import json
from collections import defaultdict

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"    # Monotonically increasing value
    GAUGE = "gauge"        # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"    # Statistical summary
    TIMER = "timer"        # Duration measurements

@dataclass
class MetricConfig:
    """Configuration for metrics collection"""
    enable_aggregation: bool = True
    aggregation_interval: int = 60  # seconds
    retention_period: int = 24 * 60 * 60  # 24 hours in seconds
    enable_persistence: bool = True
    storage_path: Optional[str] = None
    max_tags: int = 10
    max_metrics: int = 1000
    enable_percentiles: bool = True
    percentiles: List[float] = None  # e.g., [0.5, 0.9, 0.95, 0.99]

class MetricValue:
    """Represents a metric value with timestamp"""
    def __init__(self, value: float, timestamp: Optional[datetime] = None):
        self.value = value
        self.timestamp = timestamp or datetime.utcnow()
        self.tags: Dict[str, str] = {}

class MetricsCollector:
    """Collects and manages metrics"""
    def __init__(self, config: MetricConfig):
        self.config = config
        self._metrics: Dict[str, Dict[str, List[MetricValue]]] = defaultdict(lambda: defaultdict(list))
        self._aggregation_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Start metrics collector"""
        if self.config.enable_persistence:
            await self._load_state()

        if self.config.enable_aggregation:
            self._aggregation_task = asyncio.create_task(self._aggregation_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop metrics collector"""
        if self._aggregation_task:
            self._aggregation_task.cancel()
            try:
                await self._aggregation_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self.config.enable_persistence:
            await self._save_state()

    async def increment(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None
    ):
        """Increment counter metric"""
        await self._add_metric(MetricType.COUNTER, name, value, tags)

    async def gauge(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Set gauge metric"""
        await self._add_metric(MetricType.GAUGE, name, value, tags)

    async def histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record histogram metric"""
        await self._add_metric(MetricType.HISTOGRAM, name, value, tags)

    async def timing(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record timing metric"""
        await self._add_metric(MetricType.TIMER, name, value, tags)

    async def _add_metric(
        self,
        metric_type: MetricType,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Add metric value"""
        async with self._lock:
            # Validate tags
            if tags and len(tags) > self.config.max_tags:
                tags = dict(list(tags.items())[:self.config.max_tags])

            # Create metric key
            key = self._make_metric_key(name, tags)

            # Add value
            metric = MetricValue(value)
            metric.tags = tags or {}
            self._metrics[metric_type.value][key].append(metric)

            # Check max metrics limit
            if len(self._metrics[metric_type.value]) > self.config.max_metrics:
                # Remove oldest metrics
                oldest_key = min(
                    self._metrics[metric_type.value].keys(),
                    key=lambda k: min(v.timestamp for v in self._metrics[metric_type.value][k])
                )
                del self._metrics[metric_type.value][oldest_key]

    def _make_metric_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Create unique key for metric"""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"

    async def get_metric(
        self,
        name: str,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[MetricValue]:
        """Get metric values"""
        key = self._make_metric_key(name, tags)
        values = self._metrics[metric_type.value].get(key, [])

        if start_time or end_time:
            values = [
                v for v in values
                if (not start_time or v.timestamp >= start_time) and
                   (not end_time or v.timestamp <= end_time)
            ]

        return values

    async def get_stats(
        self,
        name: str,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get statistical summary of metric"""
        values = await self.get_metric(name, metric_type, tags, start_time, end_time)
        if not values:
            return {}

        numeric_values = [v.value for v in values]
        stats = {
            "count": len(values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "mean": statistics.mean(numeric_values),
            "median": statistics.median(numeric_values)
        }

        if len(numeric_values) > 1:
            stats["stddev"] = statistics.stdev(numeric_values)

        if self.config.enable_percentiles and self.config.percentiles:
            stats["percentiles"] = {
                f"p{int(p*100)}": statistics.quantiles(numeric_values, n=100)[int(p*100)-1]
                for p in self.config.percentiles
            }

        return stats

    async def _aggregation_loop(self):
        """Periodic metric aggregation"""
        while True:
            try:
                await asyncio.sleep(self.config.aggregation_interval)
                await self._aggregate_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in aggregation loop: {e}")

    async def _aggregate_metrics(self):
        """Aggregate metrics"""
        async with self._lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.config.aggregation_interval)

            for metric_type in self._metrics:
                for key in list(self._metrics[metric_type].keys()):
                    values = self._metrics[metric_type][key]
                    old_values = [v for v in values if v.timestamp < cutoff]
                    
                    if old_values:
                        # Aggregate old values
                        if metric_type == MetricType.COUNTER.value:
                            aggregated_value = sum(v.value for v in old_values)
                        else:
                            aggregated_value = statistics.mean(v.value for v in old_values)
                            
                        # Create aggregated metric
                        aggregated = MetricValue(aggregated_value, cutoff)
                        if old_values:
                            aggregated.tags = old_values[0].tags.copy()
                            
                        # Remove old values and add aggregated value
                        self._metrics[metric_type][key] = [
                            v for v in values if v.timestamp >= cutoff
                        ]
                        self._metrics[metric_type][key].append(aggregated)

    async def _cleanup_loop(self):
        """Periodic cleanup of old metrics"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check hourly
                await self._cleanup_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup loop: {e}")

    async def _cleanup_metrics(self):
        """Remove expired metrics"""
        async with self._lock:
            cutoff = datetime.utcnow() - timedelta(seconds=self.config.retention_period)
            
            for metric_type in self._metrics:
                for key in list(self._metrics[metric_type].keys()):
                    self._metrics[metric_type][key] = [
                        v for v in self._metrics[metric_type][key]
                        if v.timestamp >= cutoff
                    ]
                    
                    # Remove empty metric series
                    if not self._metrics[metric_type][key]:
                        del self._metrics[metric_type][key]

    async def _load_state(self):
        """Load metrics state from storage"""
        if not self.config.storage_path:
            return

        try:
            with open(self.config.storage_path, 'r') as f:
                data = json.load(f)
                for metric_type in data:
                    for key, values in data[metric_type].items():
                        self._metrics[metric_type][key] = [
                            MetricValue(
                                value=v["value"],
                                timestamp=datetime.fromisoformat(v["timestamp"])
                            ) for v in values
                        ]
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading metrics state: {e}")

    async def _save_state(self):
        """Save metrics state to storage"""
        if not self.config.storage_path:
            return

        try:
            with open(self.config.storage_path, 'w') as f:
                data = {
                    metric_type: {
                        key: [
                            {
                                "value": v.value,
                                "timestamp": v.timestamp.isoformat(),
                                "tags": v.tags
                            } for v in values
                        ]
                        for key, values in metrics.items()
                    }
                    for metric_type, metrics in self._metrics.items()
                }
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving metrics state: {e}") 