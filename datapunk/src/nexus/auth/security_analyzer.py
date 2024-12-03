from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import json
import re
from collections import defaultdict

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatType(Enum):
    BRUTE_FORCE = "brute_force"
    ACCOUNT_TAKEOVER = "account_takeover"
    SUSPICIOUS_ACCESS = "suspicious_access"
    CREDENTIAL_STUFFING = "credential_stuffing"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    DATA_EXFILTRATION = "data_exfiltration"

@dataclass
class SecurityEvent:
    timestamp: datetime
    event_type: str
    user_id: Optional[str]
    ip_address: str
    details: Dict
    session_id: Optional[str] = None
    device_fingerprint: Optional[str] = None
    location_info: Optional[Dict] = None

@dataclass
class ThreatIndicator:
    threat_type: ThreatType
    threat_level: ThreatLevel
    confidence: float
    affected_users: Set[str]
    affected_ips: Set[str]
    first_seen: datetime
    last_seen: datetime
    event_count: int
    details: Dict
    related_events: List[str] = field(default_factory=list)

class SecurityAnalyzer:
    def __init__(self, analysis_window: timedelta = timedelta(hours=24)):
        self.analysis_window = analysis_window
        self._events: List[SecurityEvent] = []
        self._threat_indicators: List[ThreatIndicator] = []
        self._user_patterns: Dict[str, Dict] = defaultdict(lambda: defaultdict(int))
        self._ip_patterns: Dict[str, Dict] = defaultdict(lambda: defaultdict(int))
        
    def add_event(self, event: SecurityEvent):
        """Add a security event for analysis."""
        self._events.append(event)
        self._update_patterns(event)
        self._analyze_new_event(event)
        self._cleanup_old_events()
        
    def _update_patterns(self, event: SecurityEvent):
        """Update user and IP patterns with new event."""
        timestamp = event.timestamp
        
        if event.user_id:
            patterns = self._user_patterns[event.user_id]
            patterns["event_count"] += 1
            patterns["event_types"][event.event_type] = patterns["event_types"].get(event.event_type, 0) + 1
            patterns["ips"].add(event.ip_address)
            if event.device_fingerprint:
                patterns["devices"].add(event.device_fingerprint)
            patterns["last_seen"] = timestamp
            
        patterns = self._ip_patterns[event.ip_address]
        patterns["event_count"] += 1
        patterns["event_types"][event.event_type] = patterns["event_types"].get(event.event_type, 0) + 1
        if event.user_id:
            patterns["users"].add(event.user_id)
        patterns["last_seen"] = timestamp
        
    def _analyze_new_event(self, event: SecurityEvent):
        """Analyze a new event for potential threats."""
        self._detect_brute_force(event)
        self._detect_account_takeover(event)
        self._detect_suspicious_access(event)
        self._detect_credential_stuffing(event)
        self._detect_anomalous_behavior(event)
        
    def _detect_brute_force(self, event: SecurityEvent):
        """Detect potential brute force attacks."""
        if event.event_type != "login_failure":
            return
            
        # Check for high frequency of failed logins
        if event.user_id:
            user_patterns = self._user_patterns[event.user_id]
            failed_logins = user_patterns["event_types"].get("login_failure", 0)
            if failed_logins >= 10:  # Threshold for brute force detection
                self._create_threat_indicator(
                    ThreatType.BRUTE_FORCE,
                    ThreatLevel.HIGH,
                    confidence=min(0.5 + (failed_logins / 20), 0.95),
                    affected_users={event.user_id},
                    affected_ips={event.ip_address},
                    first_seen=event.timestamp,
                    details={
                        "failed_attempts": failed_logins,
                        "timespan": "24h",
                        "pattern": "Multiple failed login attempts"
                    }
                )
                
    def _detect_account_takeover(self, event: SecurityEvent):
        """Detect potential account takeover attempts."""
        if event.event_type != "login_success" or not event.user_id:
            return
            
        user_patterns = self._user_patterns[event.user_id]
        
        # Check for login from new device/location
        if event.device_fingerprint and event.location_info:
            is_new_device = event.device_fingerprint not in user_patterns.get("devices", set())
            is_new_location = not any(
                loc.get("country") == event.location_info.get("country")
                for loc in user_patterns.get("locations", [])
            )
            
            if is_new_device and is_new_location:
                recent_failed_attempts = sum(
                    1 for e in self._events
                    if e.user_id == event.user_id
                    and e.event_type == "login_failure"
                    and event.timestamp - e.timestamp <= timedelta(hours=24)
                )
                
                if recent_failed_attempts > 0:
                    self._create_threat_indicator(
                        ThreatType.ACCOUNT_TAKEOVER,
                        ThreatLevel.HIGH,
                        confidence=0.8,
                        affected_users={event.user_id},
                        affected_ips={event.ip_address},
                        first_seen=event.timestamp,
                        details={
                            "new_device": True,
                            "new_location": True,
                            "recent_failed_attempts": recent_failed_attempts,
                            "location": event.location_info
                        }
                    )
                    
    def _detect_credential_stuffing(self, event: SecurityEvent):
        """Detect potential credential stuffing attacks."""
        if event.event_type != "login_failure":
            return
            
        ip_patterns = self._ip_patterns[event.ip_address]
        unique_users = len(ip_patterns.get("users", set()))
        
        if unique_users >= 5:  # Threshold for credential stuffing detection
            failed_ratio = ip_patterns["event_types"].get("login_failure", 0) / ip_patterns["event_count"]
            if failed_ratio > 0.8:  # High ratio of failures
                self._create_threat_indicator(
                    ThreatType.CREDENTIAL_STUFFING,
                    ThreatLevel.CRITICAL,
                    confidence=min(0.6 + (unique_users / 10), 0.95),
                    affected_users=ip_patterns["users"],
                    affected_ips={event.ip_address},
                    first_seen=event.timestamp,
                    details={
                        "unique_users_attempted": unique_users,
                        "failure_ratio": failed_ratio,
                        "total_attempts": ip_patterns["event_count"]
                    }
                )
                
    def _detect_suspicious_access(self, event: SecurityEvent):
        """Detect suspicious access patterns."""
        if not event.user_id or event.event_type not in ["login_success", "api_access"]:
            return
            
        user_patterns = self._user_patterns[event.user_id]
        
        # Check for concurrent sessions from different locations
        active_sessions = [
            e for e in self._events
            if e.user_id == event.user_id
            and e.event_type == "login_success"
            and event.timestamp - e.timestamp <= timedelta(hours=1)
            and e.location_info
        ]
        
        if len(active_sessions) > 1:
            locations = {
                (s.location_info.get("country"), s.location_info.get("city"))
                for s in active_sessions
                if s.location_info
            }
            if len(locations) > 1:
                self._create_threat_indicator(
                    ThreatType.SUSPICIOUS_ACCESS,
                    ThreatLevel.MEDIUM,
                    confidence=0.7,
                    affected_users={event.user_id},
                    affected_ips={s.ip_address for s in active_sessions},
                    first_seen=event.timestamp,
                    details={
                        "concurrent_locations": list(locations),
                        "session_count": len(active_sessions)
                    }
                )
                
    def _detect_anomalous_behavior(self, event: SecurityEvent):
        """Detect anomalous user behavior."""
        if not event.user_id:
            return
            
        user_patterns = self._user_patterns[event.user_id]
        
        # Calculate baseline activity
        hourly_events = defaultdict(int)
        for e in self._events:
            if e.user_id == event.user_id:
                hour = e.timestamp.hour
                hourly_events[hour] += 1
                
        if hourly_events:
            avg_hourly = sum(hourly_events.values()) / len(hourly_events)
            current_hour_events = hourly_events[event.timestamp.hour]
            
            if current_hour_events > avg_hourly * 3:  # Activity spike
                self._create_threat_indicator(
                    ThreatType.ANOMALOUS_BEHAVIOR,
                    ThreatLevel.MEDIUM,
                    confidence=0.6,
                    affected_users={event.user_id},
                    affected_ips={event.ip_address},
                    first_seen=event.timestamp,
                    details={
                        "average_hourly_events": avg_hourly,
                        "current_hour_events": current_hour_events,
                        "spike_factor": current_hour_events / avg_hourly
                    }
                )
                
    def _create_threat_indicator(self, threat_type: ThreatType, threat_level: ThreatLevel,
                               confidence: float, affected_users: Set[str],
                               affected_ips: Set[str], first_seen: datetime,
                               details: Dict) -> ThreatIndicator:
        """Create and store a new threat indicator."""
        indicator = ThreatIndicator(
            threat_type=threat_type,
            threat_level=threat_level,
            confidence=confidence,
            affected_users=affected_users,
            affected_ips=affected_ips,
            first_seen=first_seen,
            last_seen=datetime.utcnow(),
            event_count=1,
            details=details
        )
        self._threat_indicators.append(indicator)
        return indicator
        
    def _cleanup_old_events(self):
        """Remove events outside the analysis window."""
        cutoff = datetime.utcnow() - self.analysis_window
        self._events = [e for e in self._events if e.timestamp > cutoff]
        
    def get_active_threats(self, min_confidence: float = 0.5) -> List[ThreatIndicator]:
        """Get current active threats above confidence threshold."""
        return [
            t for t in self._threat_indicators
            if t.confidence >= min_confidence
            and datetime.utcnow() - t.last_seen <= self.analysis_window
        ]
        
    def get_user_risk_score(self, user_id: str) -> float:
        """Calculate current risk score for a user."""
        active_threats = [
            t for t in self.get_active_threats()
            if user_id in t.affected_users
        ]
        
        if not active_threats:
            return 0.0
            
        # Weight threats by level and confidence
        weights = {
            ThreatLevel.LOW: 0.25,
            ThreatLevel.MEDIUM: 0.5,
            ThreatLevel.HIGH: 0.75,
            ThreatLevel.CRITICAL: 1.0
        }
        
        scores = [
            weights[t.threat_level] * t.confidence
            for t in active_threats
        ]
        
        return min(1.0, sum(scores) / len(scores)) 