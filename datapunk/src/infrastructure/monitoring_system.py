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
import numpy as np

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

@dataclass
class HealthCheck:
    name: str
    check_function: Callable[[], bool]
    interval: timedelta
    timeout: float
    dependencies: Optional[List[str]] = None
    description: Optional[str] = None

@dataclass
class HealthStatus:
    name: str
    status: bool
    last_check: datetime
    last_success: Optional[datetime]
    last_failure: Optional[datetime]
    consecutive_failures: int
    error_message: Optional[str] = None

class AggregationMethod(Enum):
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    P95 = "p95"
    P99 = "p99"

@dataclass
class MetricAggregation:
    name: str
    source_metric: str
    method: AggregationMethod
    interval: timedelta
    labels: Optional[Dict[str, str]] = None
    filter_expr: Optional[str] = None

class MonitoringSystem:
    def __init__(
        self,
        retention_period: timedelta = timedelta(days=7),
        alert_check_interval: float = 60.0,
        cleanup_interval: float = 3600.0,
        aggregation_interval: float = 300.0  # 5 minutes
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
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_status: Dict[str, HealthStatus] = {}
        self.aggregations: Dict[str, MetricAggregation] = {}
        self.aggregated_values: Dict[str, Dict[str, List[tuple]]] = defaultdict(lambda: defaultdict(list))
        self.aggregation_interval = aggregation_interval

    async def start(self) -> None:
        """Start the monitoring system."""
        self._running = True
        self._tasks = [
            asyncio.create_task(self._check_alerts()),
            asyncio.create_task(self._cleanup_old_data()),
            asyncio.create_task(self._run_health_checks()),
            asyncio.create_task(self._run_aggregations())
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

    def register_health_check(self, check: HealthCheck) -> None:
        """Register a new health check."""
        with self._lock:
            if check.name in self.health_checks:
                raise ValueError(f"Health check {check.name} already registered")
            
            # Validate dependencies
            if check.dependencies:
                missing_deps = [
                    dep for dep in check.dependencies 
                    if dep not in self.health_checks
                ]
                if missing_deps:
                    raise ValueError(f"Missing dependencies: {missing_deps}")
            
            self.health_checks[check.name] = check
            self.health_status[check.name] = HealthStatus(
                name=check.name,
                status=True,
                last_check=datetime.now(),
                last_success=datetime.now(),
                last_failure=None,
                consecutive_failures=0
            )

    def register_aggregation(self, aggregation: MetricAggregation) -> None:
        """Register a new metric aggregation."""
        with self._lock:
            if aggregation.name in self.aggregations:
                raise ValueError(f"Aggregation {aggregation.name} already registered")
            if aggregation.source_metric not in self.metrics:
                raise ValueError(f"Source metric {aggregation.source_metric} not registered")
            
            self.aggregations[aggregation.name] = aggregation

    def get_health_status(
        self,
        check_names: Optional[List[str]] = None
    ) -> Dict[str, HealthStatus]:
        """Get health status for specified checks or all checks."""
        with self._lock:
            if not check_names:
                return dict(self.health_status)
            return {
                name: status 
                for name, status in self.health_status.items()
                if name in check_names
            }

    def get_aggregated_values(
        self,
        aggregation_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[tuple]:
        """Get aggregated values for a specific aggregation."""
        with self._lock:
            if aggregation_name not in self.aggregations:
                raise ValueError(f"Aggregation {aggregation_name} not registered")

            values = []
            for label_key, stored_values in self.aggregated_values[aggregation_name].items():
                filtered_values = [
                    (ts, val) for ts, val in stored_values
                    if (not start_time or ts >= start_time) and
                       (not end_time or ts <= end_time)
                ]
                values.extend(filtered_values)

            return sorted(values, key=lambda x: x[0])

    async def _run_health_checks(self) -> None:
        """Run health checks periodically."""
        while self._running:
            try:
                checks_to_run = []
                current_time = datetime.now()
                
                with self._lock:
                    for name, check in self.health_checks.items():
                        status = self.health_status[name]
                        if current_time - status.last_check >= check.interval:
                            checks_to_run.append((name, check))

                for name, check in checks_to_run:
                    await self._run_single_health_check(name, check)
                
                # Find shortest interval for next check
                next_check = min(
                    (
                        check.interval - (current_time - self.health_status[name].last_check)
                        for name, check in self.health_checks.items()
                    ),
                    default=timedelta(minutes=1)
                )
                
                await asyncio.sleep(max(0.1, next_check.total_seconds()))
            except Exception as e:
                self.logger.error(f"Error running health checks: {str(e)}")
                await asyncio.sleep(60)

    async def _run_single_health_check(
        self,
        name: str,
        check: HealthCheck
    ) -> None:
        """Run a single health check."""
        try:
            # Check dependencies first
            if check.dependencies:
                for dep in check.dependencies:
                    if not self.health_status[dep].status:
                        raise ValueError(f"Dependency {dep} is unhealthy")

            # Run the check with timeout
            try:
                async with asyncio.timeout(check.timeout):
                    status = await asyncio.to_thread(check.check_function)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Health check {name} timed out")

            with self._lock:
                current_status = self.health_status[name]
                if status:
                    self.health_status[name] = HealthStatus(
                        name=name,
                        status=True,
                        last_check=datetime.now(),
                        last_success=datetime.now(),
                        last_failure=current_status.last_failure,
                        consecutive_failures=0
                    )
                else:
                    self.health_status[name] = HealthStatus(
                        name=name,
                        status=False,
                        last_check=datetime.now(),
                        last_success=current_status.last_success,
                        last_failure=datetime.now(),
                        consecutive_failures=current_status.consecutive_failures + 1,
                        error_message="Check returned False"
                    )

        except Exception as e:
            with self._lock:
                current_status = self.health_status[name]
                self.health_status[name] = HealthStatus(
                    name=name,
                    status=False,
                    last_check=datetime.now(),
                    last_success=current_status.last_success,
                    last_failure=datetime.now(),
                    consecutive_failures=current_status.consecutive_failures + 1,
                    error_message=str(e)
                )

    async def _run_aggregations(self) -> None:
        """Run metric aggregations periodically."""
        while self._running:
            try:
                current_time = datetime.now()
                
                with self._lock:
                    for agg_name, aggregation in self.aggregations.items():
                        self._compute_aggregation(aggregation, current_time)
                
                await asyncio.sleep(self.aggregation_interval)
            except Exception as e:
                self.logger.error(f"Error running aggregations: {str(e)}")
                await asyncio.sleep(60)

    def _compute_aggregation(
        self,
        aggregation: MetricAggregation,
        current_time: datetime
    ) -> None:
        """Compute a single metric aggregation."""
        try:
            # Get source metric values
            start_time = current_time - aggregation.interval
            values = self.get_metric_values(
                aggregation.source_metric,
                start_time=start_time,
                end_time=current_time,
                labels=aggregation.labels
            )

            if not values:
                return

            # Extract just the values
            metric_values = [v[1] for v in values]

            # Compute aggregation
            if aggregation.method == AggregationMethod.SUM:
                result = sum(metric_values)
            elif aggregation.method == AggregationMethod.AVG:
                result = statistics.mean(metric_values)
            elif aggregation.method == AggregationMethod.MIN:
                result = min(metric_values)
            elif aggregation.method == AggregationMethod.MAX:
                result = max(metric_values)
            elif aggregation.method == AggregationMethod.COUNT:
                result = len(metric_values)
            elif aggregation.method == AggregationMethod.P95:
                result = np.percentile(metric_values, 95)
            elif aggregation.method == AggregationMethod.P99:
                result = np.percentile(metric_values, 99)
            else:
                raise ValueError(f"Unknown aggregation method: {aggregation.method}")

            # Store result
            label_key = json.dumps(aggregation.labels, sort_keys=True) if aggregation.labels else "default"
            self.aggregated_values[aggregation.name][label_key].append(
                (current_time, result)
            )

        except Exception as e:
            self.logger.error(f"Error computing aggregation {aggregation.name}: {str(e)}")

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
                    
                    # Clean up aggregated values
                    for agg_name in self.aggregated_values:
                        for label_key in list(self.aggregated_values[agg_name].keys()):
                            self.aggregated_values[agg_name][label_key] = [
                                (ts, val) for ts, val in self.aggregated_values[agg_name][label_key]
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