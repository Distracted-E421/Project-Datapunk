from typing import Dict, List, Optional, Set
import time
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
from .security_metrics import SecurityMetrics
from .security_audit import SecurityAuditor, AuditEvent, AuditEventType

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ThreatRule:
    name: str
    threshold: int
    time_window: int  # seconds
    threat_level: ThreatLevel
    cooldown: int  # seconds

@dataclass
class ThreatEvent:
    service_id: str
    source_ip: str
    event_type: str
    timestamp: float
    details: Dict[str, any]

class ThreatDetector:
    def __init__(
        self,
        security_metrics: SecurityMetrics,
        security_auditor: SecurityAuditor
    ):
        self.security_metrics = security_metrics
        self.security_auditor = security_auditor
        self.logger = logging.getLogger(__name__)
        
        # Event tracking
        self.events: Dict[str, List[ThreatEvent]] = defaultdict(list)
        self.blocked_ips: Set[str] = set()
        self.cooldowns: Dict[str, float] = {}
        
        # Default rules
        self.rules: Dict[str, ThreatRule] = {
            "auth_failure": ThreatRule(
                name="Authentication Failures",
                threshold=5,
                time_window=300,  # 5 minutes
                threat_level=ThreatLevel.HIGH,
                cooldown=1800  # 30 minutes
            ),
            "rate_limit": ThreatRule(
                name="Rate Limit Breaches",
                threshold=10,
                time_window=60,  # 1 minute
                threat_level=ThreatLevel.MEDIUM,
                cooldown=600  # 10 minutes
            ),
            "access_denied": ThreatRule(
                name="Access Denied",
                threshold=3,
                time_window=60,  # 1 minute
                threat_level=ThreatLevel.HIGH,
                cooldown=900  # 15 minutes
            )
        }

    async def process_event(self, event: ThreatEvent) -> Optional[ThreatLevel]:
        """Process a new security event and detect threats"""
        try:
            # Skip if IP is in cooldown
            if event.source_ip in self.cooldowns:
                if time.time() < self.cooldowns[event.source_ip]:
                    return None
                del self.cooldowns[event.source_ip]

            # Add event to tracking
            self.events[event.source_ip].append(event)
            
            # Clean old events
            await self._clean_old_events()

            # Check rules
            threat_level = await self._check_rules(event.source_ip)
            if threat_level:
                await self._handle_threat(event, threat_level)
            
            return threat_level

        except Exception as e:
            self.logger.error(f"Failed to process security event: {str(e)}")
            return None

    async def _check_rules(self, source_ip: str) -> Optional[ThreatLevel]:
        """Check all rules against events from an IP"""
        try:
            current_time = time.time()
            highest_threat = None

            for rule_name, rule in self.rules.items():
                # Count events in time window
                count = sum(
                    1 for event in self.events[source_ip]
                    if event.event_type == rule_name
                    and current_time - event.timestamp <= rule.time_window
                )

                if count >= rule.threshold:
                    if not highest_threat or rule.threat_level.value > highest_threat.value:
                        highest_threat = rule.threat_level

            return highest_threat

        except Exception as e:
            self.logger.error(f"Failed to check threat rules: {str(e)}")
            return None

    async def _handle_threat(self, event: ThreatEvent, threat_level: ThreatLevel) -> None:
        """Handle detected threat"""
        try:
            # Block IP for high/critical threats
            if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                self.blocked_ips.add(event.source_ip)
                cooldown_time = max(
                    rule.cooldown for rule in self.rules.values()
                    if rule.threat_level == threat_level
                )
                self.cooldowns[event.source_ip] = time.time() + cooldown_time

            # Log audit event
            await self.security_auditor.log_event(
                AuditEvent(
                    event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
                    service_id=event.service_id,
                    timestamp=time.time(),
                    details={
                        "threat_level": threat_level.value,
                        "source_ip": event.source_ip,
                        "original_event": event.details
                    },
                    source_ip=event.source_ip,
                    severity="CRITICAL" if threat_level == ThreatLevel.CRITICAL else "WARNING"
                )
            )

            # Update metrics
            await self.security_metrics.record_suspicious_activity(
                event.service_id,
                f"threat_{threat_level.value}",
                event.details
            )

        except Exception as e:
            self.logger.error(f"Failed to handle threat: {str(e)}")

    async def _clean_old_events(self) -> None:
        """Clean up old events beyond the longest time window"""
        try:
            max_window = max(rule.time_window for rule in self.rules.values())
            cutoff_time = time.time() - max_window

            for ip in list(self.events.keys()):
                self.events[ip] = [
                    event for event in self.events[ip]
                    if event.timestamp > cutoff_time
                ]
                if not self.events[ip]:
                    del self.events[ip]

        except Exception as e:
            self.logger.error(f"Failed to clean old events: {str(e)}") 