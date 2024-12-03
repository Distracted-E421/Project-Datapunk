import pytest
from datetime import datetime, timedelta
from src.nexus.auth.security_analyzer import (
    SecurityAnalyzer,
    SecurityEvent,
    ThreatType,
    ThreatLevel,
    ThreatIndicator
)

@pytest.fixture
def security_analyzer():
    return SecurityAnalyzer(analysis_window=timedelta(hours=1))

@pytest.fixture
def sample_event():
    return SecurityEvent(
        timestamp=datetime.utcnow(),
        event_type="login_success",
        user_id="test_user",
        ip_address="192.168.1.1",
        details={},
        session_id="test_session",
        device_fingerprint="test_device",
        location_info={"country": "US", "city": "New York"}
    )

def test_event_processing(security_analyzer, sample_event):
    # Add event
    security_analyzer.add_event(sample_event)
    
    # Check patterns were updated
    user_patterns = security_analyzer._user_patterns[sample_event.user_id]
    assert user_patterns["event_count"] == 1
    assert user_patterns["event_types"]["login_success"] == 1
    
    ip_patterns = security_analyzer._ip_patterns[sample_event.ip_address]
    assert ip_patterns["event_count"] == 1
    assert ip_patterns["event_types"]["login_success"] == 1

def test_brute_force_detection(security_analyzer):
    user_id = "test_user"
    ip_address = "192.168.1.1"
    
    # Generate failed login attempts
    for _ in range(10):
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type="login_failure",
            user_id=user_id,
            ip_address=ip_address,
            details={"reason": "invalid_password"}
        )
        security_analyzer.add_event(event)
    
    # Check for brute force threat
    threats = security_analyzer.get_active_threats()
    brute_force_threats = [
        t for t in threats
        if t.threat_type == ThreatType.BRUTE_FORCE
    ]
    
    assert len(brute_force_threats) > 0
    threat = brute_force_threats[0]
    assert threat.threat_level == ThreatLevel.HIGH
    assert user_id in threat.affected_users
    assert ip_address in threat.affected_ips

def test_account_takeover_detection(security_analyzer):
    user_id = "test_user"
    
    # Generate failed login attempts
    for _ in range(5):
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type="login_failure",
            user_id=user_id,
            ip_address="192.168.1.1",
            details={"reason": "invalid_password"}
        )
        security_analyzer.add_event(event)
    
    # Successful login from new device/location
    success_event = SecurityEvent(
        timestamp=datetime.utcnow(),
        event_type="login_success",
        user_id=user_id,
        ip_address="10.0.0.1",
        details={},
        device_fingerprint="new_device",
        location_info={"country": "FR", "city": "Paris"}
    )
    security_analyzer.add_event(success_event)
    
    # Check for account takeover threat
    threats = security_analyzer.get_active_threats()
    takeover_threats = [
        t for t in threats
        if t.threat_type == ThreatType.ACCOUNT_TAKEOVER
    ]
    
    assert len(takeover_threats) > 0
    threat = takeover_threats[0]
    assert threat.threat_level == ThreatLevel.HIGH
    assert user_id in threat.affected_users

def test_credential_stuffing_detection(security_analyzer):
    ip_address = "192.168.1.1"
    
    # Generate failed login attempts for multiple users
    for i in range(10):
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type="login_failure",
            user_id=f"user_{i}",
            ip_address=ip_address,
            details={"reason": "invalid_password"}
        )
        security_analyzer.add_event(event)
    
    # Check for credential stuffing threat
    threats = security_analyzer.get_active_threats()
    stuffing_threats = [
        t for t in threats
        if t.threat_type == ThreatType.CREDENTIAL_STUFFING
    ]
    
    assert len(stuffing_threats) > 0
    threat = stuffing_threats[0]
    assert threat.threat_level == ThreatLevel.CRITICAL
    assert ip_address in threat.affected_ips
    assert len(threat.affected_users) >= 5

def test_suspicious_access_detection(security_analyzer):
    user_id = "test_user"
    
    # Login from different locations
    locations = [
        {"country": "US", "city": "New York"},
        {"country": "FR", "city": "Paris"},
        {"country": "JP", "city": "Tokyo"}
    ]
    
    for i, location in enumerate(locations):
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type="login_success",
            user_id=user_id,
            ip_address=f"192.168.1.{i}",
            details={},
            location_info=location
        )
        security_analyzer.add_event(event)
    
    # Check for suspicious access threat
    threats = security_analyzer.get_active_threats()
    suspicious_threats = [
        t for t in threats
        if t.threat_type == ThreatType.SUSPICIOUS_ACCESS
    ]
    
    assert len(suspicious_threats) > 0
    threat = suspicious_threats[0]
    assert threat.threat_level == ThreatLevel.MEDIUM
    assert user_id in threat.affected_users

def test_anomalous_behavior_detection(security_analyzer):
    user_id = "test_user"
    
    # Generate normal activity pattern
    for _ in range(5):
        event = SecurityEvent(
            timestamp=datetime.utcnow() - timedelta(minutes=30),
            event_type="api_access",
            user_id=user_id,
            ip_address="192.168.1.1",
            details={}
        )
        security_analyzer.add_event(event)
    
    # Generate spike in activity
    for _ in range(20):
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type="api_access",
            user_id=user_id,
            ip_address="192.168.1.1",
            details={}
        )
        security_analyzer.add_event(event)
    
    # Check for anomalous behavior threat
    threats = security_analyzer.get_active_threats()
    anomaly_threats = [
        t for t in threats
        if t.threat_type == ThreatType.ANOMALOUS_BEHAVIOR
    ]
    
    assert len(anomaly_threats) > 0
    threat = anomaly_threats[0]
    assert threat.threat_level == ThreatLevel.MEDIUM
    assert user_id in threat.affected_users

def test_risk_score_calculation(security_analyzer):
    user_id = "test_user"
    
    # Add some suspicious events
    security_analyzer._threat_indicators.append(
        ThreatIndicator(
            threat_type=ThreatType.BRUTE_FORCE,
            threat_level=ThreatLevel.HIGH,
            confidence=0.8,
            affected_users={user_id},
            affected_ips={"192.168.1.1"},
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            event_count=1,
            details={}
        )
    )
    
    security_analyzer._threat_indicators.append(
        ThreatIndicator(
            threat_type=ThreatType.SUSPICIOUS_ACCESS,
            threat_level=ThreatLevel.MEDIUM,
            confidence=0.6,
            affected_users={user_id},
            affected_ips={"192.168.1.2"},
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            event_count=1,
            details={}
        )
    )
    
    # Calculate risk score
    risk_score = security_analyzer.get_user_risk_score(user_id)
    assert 0.5 < risk_score < 1.0

def test_event_cleanup(security_analyzer, sample_event):
    # Add old event
    old_event = SecurityEvent(
        timestamp=datetime.utcnow() - timedelta(hours=2),
        event_type="login_success",
        user_id="test_user",
        ip_address="192.168.1.1",
        details={}
    )
    security_analyzer.add_event(old_event)
    
    # Add recent event
    security_analyzer.add_event(sample_event)
    
    # Old event should be cleaned up
    assert len(security_analyzer._events) == 1
    assert security_analyzer._events[0].timestamp == sample_event.timestamp 