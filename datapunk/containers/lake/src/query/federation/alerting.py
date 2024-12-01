from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import logging
from enum import Enum

class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertType(Enum):
    """Types of alerts that can be generated."""
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    ERROR = "error"
    SECURITY = "security"
    AVAILABILITY = "availability"

@dataclass
class AlertRule:
    """Definition of an alert rule."""
    name: str
    description: str
    severity: AlertSeverity
    alert_type: AlertType
    condition: Callable[[Dict[str, Any]], bool]
    cooldown_minutes: int = 15
    last_triggered: Optional[datetime] = None

@dataclass
class Alert:
    """Alert instance."""
    rule_name: str
    severity: AlertSeverity
    alert_type: AlertType
    message: str
    timestamp: datetime
    context: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_message: Optional[str] = None

class AlertManager:
    """Manages alert rules and alert generation."""
    
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.handlers: Dict[AlertSeverity, List[Callable[[Alert], None]]] = {
            severity: [] for severity in AlertSeverity
        }
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add a new alert rule."""
        self.rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str) -> None:
        """Remove an alert rule."""
        if rule_name in self.rules:
            del self.rules[rule_name]
    
    def add_handler(self,
                   severity: AlertSeverity,
                   handler: Callable[[Alert], None]) -> None:
        """Add an alert handler for a specific severity level."""
        self.handlers[severity].append(handler)
    
    async def check_conditions(self, metrics: Dict[str, Any]) -> None:
        """Check all alert conditions against current metrics."""
        try:
            async with self._lock:
                for rule in self.rules.values():
                    # Check cooldown
                    if rule.last_triggered:
                        cooldown_end = rule.last_triggered + timedelta(
                            minutes=rule.cooldown_minutes
                        )
                        if datetime.utcnow() < cooldown_end:
                            continue
                    
                    # Check condition
                    try:
                        if rule.condition(metrics):
                            await self._create_alert(rule, metrics)
                            rule.last_triggered = datetime.utcnow()
                    except Exception as e:
                        self.logger.error(
                            f"Error checking condition for rule {rule.name}: {e}"
                        )
        except Exception as e:
            self.logger.error(f"Error checking alert conditions: {e}")
    
    async def _create_alert(self,
                          rule: AlertRule,
                          context: Dict[str, Any]) -> None:
        """Create and process a new alert."""
        try:
            alert = Alert(
                rule_name=rule.name,
                severity=rule.severity,
                alert_type=rule.alert_type,
                message=rule.description,
                timestamp=datetime.utcnow(),
                context=context
            )
            
            # Add to active alerts
            self.active_alerts.append(alert)
            
            # Call handlers
            for handler in self.handlers[rule.severity]:
                try:
                    handler(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert handler: {e}")
            
            self.logger.info(
                f"Created {rule.severity.value} alert: {rule.name}"
            )
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
    
    async def resolve_alert(self,
                          alert_id: int,
                          resolution_message: str) -> None:
        """Resolve an active alert."""
        try:
            async with self._lock:
                if 0 <= alert_id < len(self.active_alerts):
                    alert = self.active_alerts[alert_id]
                    alert.resolved = True
                    alert.resolved_at = datetime.utcnow()
                    alert.resolution_message = resolution_message
                    
                    # Move to history
                    self.alert_history.append(alert)
                    self.active_alerts.pop(alert_id)
                    
                    self.logger.info(
                        f"Resolved alert {alert.rule_name}: {resolution_message}"
                    )
                    
                    # Trim history
                    await self._trim_history()
        except Exception as e:
            self.logger.error(f"Error resolving alert: {e}")
    
    def get_active_alerts(self,
                         severity: Optional[AlertSeverity] = None,
                         alert_type: Optional[AlertType] = None) -> List[Alert]:
        """Get active alerts with optional filtering."""
        alerts = self.active_alerts
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
            
        return alerts
    
    def get_alert_history(self,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         severity: Optional[AlertSeverity] = None,
                         alert_type: Optional[AlertType] = None) -> List[Alert]:
        """Get historical alerts with filtering."""
        if not start_time:
            start_time = datetime.min
        if not end_time:
            end_time = datetime.max
            
        alerts = [
            alert for alert in self.alert_history
            if start_time <= alert.timestamp <= end_time
        ]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
            
        return alerts
    
    def get_alert_stats(self,
                       hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for a time period."""
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            alerts = self.get_alert_history(start_time=start_time)
            
            # Calculate statistics
            total_alerts = len(alerts)
            if total_alerts == 0:
                return {
                    'total_alerts': 0,
                    'alerts_by_severity': {},
                    'alerts_by_type': {},
                    'avg_resolution_time_minutes': 0,
                    'unresolved_alerts': 0
                }
            
            # Count by severity and type
            severity_counts = {
                severity.value: 0 for severity in AlertSeverity
            }
            type_counts = {
                alert_type.value: 0 for alert_type in AlertType
            }
            
            resolution_times = []
            unresolved = 0
            
            for alert in alerts:
                severity_counts[alert.severity.value] += 1
                type_counts[alert.alert_type.value] += 1
                
                if alert.resolved and alert.resolved_at:
                    resolution_time = (
                        alert.resolved_at - alert.timestamp
                    ).total_seconds() / 60  # Convert to minutes
                    resolution_times.append(resolution_time)
                else:
                    unresolved += 1
            
            return {
                'total_alerts': total_alerts,
                'alerts_by_severity': severity_counts,
                'alerts_by_type': type_counts,
                'avg_resolution_time_minutes': (
                    sum(resolution_times) / len(resolution_times)
                    if resolution_times else 0
                ),
                'unresolved_alerts': unresolved
            }
        except Exception as e:
            self.logger.error(f"Error generating alert stats: {e}")
            return {}
    
    async def _trim_history(self) -> None:
        """Trim alert history to prevent memory growth."""
        try:
            # Keep last 30 days of alerts
            cutoff = datetime.utcnow() - timedelta(days=30)
            self.alert_history = [
                alert for alert in self.alert_history
                if alert.timestamp >= cutoff
            ]
        except Exception as e:
            self.logger.error(f"Error trimming alert history: {e}")

# Default alert rules
def create_default_rules() -> List[AlertRule]:
    """Create default alert rules."""
    return [
        AlertRule(
            name="high_error_rate",
            description="Error rate exceeded threshold",
            severity=AlertSeverity.ERROR,
            alert_type=AlertType.ERROR,
            condition=lambda m: m.get('error_rate', 0) > 0.1
        ),
        AlertRule(
            name="high_latency",
            description="Query latency exceeded threshold",
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.PERFORMANCE,
            condition=lambda m: m.get('avg_execution_time_ms', 0) > 1000
        ),
        AlertRule(
            name="low_cache_hit_ratio",
            description="Cache hit ratio below threshold",
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.PERFORMANCE,
            condition=lambda m: m.get('cache_hit_ratio', 1) < 0.5
        ),
        AlertRule(
            name="high_memory_usage",
            description="Memory usage exceeded threshold",
            severity=AlertSeverity.WARNING,
            alert_type=AlertType.RESOURCE,
            condition=lambda m: m.get('memory_usage_mb', 0) > 1000
        ),
        AlertRule(
            name="source_unavailable",
            description="Data source is unavailable",
            severity=AlertSeverity.CRITICAL,
            alert_type=AlertType.AVAILABILITY,
            condition=lambda m: any(
                s.get('status') == 'unavailable'
                for s in m.get('source_stats', {}).values()
            )
        )
    ]