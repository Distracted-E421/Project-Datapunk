import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime, timedelta
import asyncio
from enum import Enum
import json
import statistics
from threading import Lock
from collections import defaultdict

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricDefinition:
    name: str
    type: MetricType
    description: str
    labels: Set[str]
    unit: Optional[str] = None

@dataclass
class AlertRule:
    name: str
    metric_name: str
    condition: str  # Python expression as string
    severity: AlertSeverity
    duration: timedelta
    labels: Optional[Dict[str, str]] = None
    description: Optional[str] = None

@dataclass
class Alert:
    rule: AlertRule
    value: float
    timestamp: datetime
    labels: Dict[str, str]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class MonitoringSystem:
    def __init__(
        self,
        retention_period: timedelta = timedelta(days=7),
        alert_check_interval: float = 60.0,
        cleanup_interval: float = 3600.0
    ):
        self.metrics: Dict[str, MetricDefinition] = {}
        self.metric_values: Dict[str, Dict[str, List[tuple]]] = defaultdict(lambda: defaultdict(list))
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.retention_period = retention_period
        self.alert_check_interval = alert_check_interval
        self.cleanup_interval = cleanup_interval
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self) -> None:
        """Start the monitoring system."""
        self._running = True
        self._tasks = [
            asyncio.create_task(self._check_alerts()),
            asyncio.create_task(self._cleanup_old_data())
        ]

    async def stop(self) -> None:
        """Stop the monitoring system."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

    def register_metric(self, metric: MetricDefinition) -> None:
        """Register a new metric."""
        with self._lock:
            if metric.name in self.metrics:
                raise ValueError(f"Metric {metric.name} already registered")
            self.metrics[metric.name] = metric
            self.logger.info(f"Registered metric: {metric.name}")

    def register_alert_rule(self, rule: AlertRule) -> None:
        """Register a new alert rule."""
        with self._lock:
            if rule.name in self.alert_rules:
                raise ValueError(f"Alert rule {rule.name} already registered")
            if rule.metric_name not in self.metrics:
                raise ValueError(f"Metric {rule.metric_name} not registered")
            self.alert_rules[rule.name] = rule
            self.logger.info(f"Registered alert rule: {rule.name}")

    def record_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric value."""
        with self._lock:
            if metric_name not in self.metrics:
                raise ValueError(f"Metric {metric_name} not registered")

            metric_def = self.metrics[metric_name]
            labels = labels or {}

            # Validate labels
            if not metric_def.labels.issubset(labels.keys()):
                raise ValueError(f"Missing required labels: {metric_def.labels - labels.keys()}")

            # Create label key for storage
            label_key = json.dumps(labels, sort_keys=True)
            
            # Store value with timestamp
            self.metric_values[metric_name][label_key].append(
                (datetime.now(), value)
            )

    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add a callback for alert notifications."""
        self._alert_callbacks.append(callback)

    def get_metric_values(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[tuple]:
        """Get metric values with optional filtering."""
        with self._lock:
            if metric_name not in self.metrics:
                raise ValueError(f"Metric {metric_name} not registered")

            values = []
            label_key = json.dumps(labels, sort_keys=True) if labels else None

            for stored_label_key, stored_values in self.metric_values[metric_name].items():
                if label_key and stored_label_key != label_key:
                    continue

                filtered_values = [
                    (ts, val) for ts, val in stored_values
                    if (not start_time or ts >= start_time) and
                       (not end_time or ts <= end_time)
                ]
                values.extend(filtered_values)

            return sorted(values, key=lambda x: x[0])

    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get active alerts with optional severity filter."""
        with self._lock:
            if not severity:
                return list(self.active_alerts)
            return [a for a in self.active_alerts if a.rule.severity == severity]

    def get_alert_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get alert history with optional filtering."""
        alerts = self.alert_history
        
        if start_time:
            alerts = [a for a in alerts if a.timestamp >= start_time]
        if end_time:
            alerts = [a for a in alerts if a.timestamp <= end_time]
        if severity:
            alerts = [a for a in alerts if a.rule.severity == severity]
            
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    async def _check_alerts(self) -> None:
        """Periodically check alert conditions."""
        while self._running:
            try:
                with self._lock:
                    for rule in self.alert_rules.values():
                        self._evaluate_alert_rule(rule)
                
                await asyncio.sleep(self.alert_check_interval)
            except Exception as e:
                self.logger.error(f"Error checking alerts: {str(e)}")
                await asyncio.sleep(self.alert_check_interval)

    def _evaluate_alert_rule(self, rule: AlertRule) -> None:
        """Evaluate a single alert rule."""
        try:
            # Get recent metric values
            end_time = datetime.now()
            start_time = end_time - rule.duration
            values = self.get_metric_values(
                rule.metric_name,
                start_time=start_time,
                end_time=end_time,
                labels=rule.labels
            )

            if not values:
                return

            # Calculate value for condition
            if self.metrics[rule.metric_name].type == MetricType.COUNTER:
                value = values[-1][1] - values[0][1]  # Delta
            elif self.metrics[rule.metric_name].type == MetricType.GAUGE:
                value = values[-1][1]  # Latest value
            else:  # HISTOGRAM or SUMMARY
                value = statistics.mean([v[1] for v in values])

            # Evaluate condition
            condition_vars = {'value': value}
            if eval(rule.condition, {}, condition_vars):
                self._create_alert(rule, value)
            else:
                self._resolve_alerts(rule)

        except Exception as e:
            self.logger.error(f"Error evaluating rule {rule.name}: {str(e)}")

    def _create_alert(self, rule: AlertRule, value: float) -> None:
        """Create a new alert if one doesn't exist."""
        # Check if alert already exists
        for alert in self.active_alerts:
            if alert.rule.name == rule.name:
                return

        # Create new alert
        alert = Alert(
            rule=rule,
            value=value,
            timestamp=datetime.now(),
            labels=rule.labels or {}
        )
        self.active_alerts.append(alert)
        self.alert_history.append(alert)

        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {str(e)}")

    def _resolve_alerts(self, rule: AlertRule) -> None:
        """Resolve alerts for a rule."""
        resolved = []
        for alert in self.active_alerts:
            if alert.rule.name == rule.name:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                resolved.append(alert)

        for alert in resolved:
            self.active_alerts.remove(alert)

    async def _cleanup_old_data(self) -> None:
        """Periodically clean up old metric data and alerts."""
        while self._running:
            try:
                cutoff_time = datetime.now() - self.retention_period
                
                with self._lock:
                    # Clean up metric values
                    for metric_name in self.metric_values:
                        for label_key in list(self.metric_values[metric_name].keys()):
                            self.metric_values[metric_name][label_key] = [
                                (ts, val) for ts, val in self.metric_values[metric_name][label_key]
                                if ts > cutoff_time
                            ]
                            
                    # Clean up alert history
                    self.alert_history = [
                        alert for alert in self.alert_history
                        if alert.timestamp > cutoff_time
                    ]
                
                await asyncio.sleep(self.cleanup_interval)
            except Exception as e:
                self.logger.error(f"Error cleaning up old data: {str(e)}")
                await asyncio.sleep(self.cleanup_interval)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        summary = {}
        with self._lock:
            for metric_name, metric_def in self.metrics.items():
                metric_summary = {
                    'type': metric_def.type.value,
                    'description': metric_def.description,
                    'unit': metric_def.unit,
                    'labels': list(metric_def.labels),
                    'values': {}
                }

                for label_key, values in self.metric_values[metric_name].items():
                    if not values:
                        continue

                    labels = json.loads(label_key)
                    latest_value = values[-1][1]
                    
                    if len(values) > 1:
                        metric_summary['values'][label_key] = {
                            'current': latest_value,
                            'min': min(v[1] for v in values),
                            'max': max(v[1] for v in values),
                            'avg': statistics.mean(v[1] for v in values)
                        }
                    else:
                        metric_summary['values'][label_key] = {
                            'current': latest_value
                        }

                summary[metric_name] = metric_summary 

        return summary 