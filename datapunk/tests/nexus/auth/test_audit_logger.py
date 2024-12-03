import pytest
import json
import os
import tempfile
from datetime import datetime
from src.nexus.auth.audit_logger import (
    SecurityAuditLogger,
    SecurityEvent,
    SecurityEventType
)

@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    fd, path = tempfile.mkstemp()
    yield path
    os.close(fd)
    os.unlink(path)

@pytest.fixture
def audit_logger(temp_log_file):
    return SecurityAuditLogger(temp_log_file, "test_system")

def test_security_event_creation():
    event = SecurityEvent(
        timestamp=datetime.utcnow(),
        event_type=SecurityEventType.LOGIN_SUCCESS,
        user_id="test_user",
        service_id=None,
        ip_address="127.0.0.1",
        details={"browser": "Chrome"}
    )
    
    # Check event ID generation
    assert len(event.event_id) == 32
    
    # Check dictionary conversion
    event_dict = event.to_dict()
    assert event_dict["event_type"] == "login_success"
    assert event_dict["user_id"] == "test_user"
    assert event_dict["ip_address"] == "127.0.0.1"
    assert event_dict["details"]["browser"] == "Chrome"

def test_log_auth_event(audit_logger, temp_log_file):
    # Log an authentication event
    audit_logger.log_auth_event(
        SecurityEventType.LOGIN_SUCCESS,
        "test_user",
        "127.0.0.1",
        browser="Chrome",
        location="US"
    )
    
    # Read log file
    with open(temp_log_file, 'r') as f:
        log_line = f.readline()
        
    # Parse JSON from log
    log_data = json.loads(log_line.split(" - ")[-1])
    
    assert log_data["event_type"] == "login_success"
    assert log_data["user_id"] == "test_user"
    assert log_data["ip_address"] == "127.0.0.1"
    assert log_data["details"]["browser"] == "Chrome"
    assert log_data["details"]["location"] == "US"
    assert log_data["system"] == "test_system"

def test_log_service_event(audit_logger, temp_log_file):
    # Log a service event
    audit_logger.log_service_event(
        SecurityEventType.CERTIFICATE_ISSUED,
        "test_service",
        "127.0.0.1",
        cert_fingerprint="abc123",
        validity_days=365
    )
    
    # Read log file
    with open(temp_log_file, 'r') as f:
        log_line = f.readline()
        
    # Parse JSON from log
    log_data = json.loads(log_line.split(" - ")[-1])
    
    assert log_data["event_type"] == "certificate_issued"
    assert log_data["service_id"] == "test_service"
    assert log_data["details"]["cert_fingerprint"] == "abc123"
    assert log_data["details"]["validity_days"] == 365

def test_log_security_event(audit_logger, temp_log_file):
    # Log a security event
    audit_logger.log_security_event(
        SecurityEventType.SUSPICIOUS_ACTIVITY,
        "127.0.0.1",
        user_id="test_user",
        reason="Multiple failed attempts",
        attempt_count=5
    )
    
    # Read log file
    with open(temp_log_file, 'r') as f:
        log_line = f.readline()
        
    # Parse JSON from log
    log_data = json.loads(log_line.split(" - ")[-1])
    
    assert log_data["event_type"] == "suspicious_activity"
    assert log_data["user_id"] == "test_user"
    assert log_data["details"]["reason"] == "Multiple failed attempts"
    assert log_data["details"]["attempt_count"] == 5

def test_critical_event_logging(audit_logger, temp_log_file):
    # Log a critical event
    audit_logger.log_security_event(
        SecurityEventType.RATE_LIMIT_EXCEEDED,
        "127.0.0.1",
        user_id="test_user"
    )
    
    # Read log file
    with open(temp_log_file, 'r') as f:
        log_lines = f.readlines()
        
    # Should have both INFO and WARNING logs
    assert len(log_lines) == 2
    assert "INFO" in log_lines[0]
    assert "WARNING" in log_lines[1]
    assert "Critical security event" in log_lines[1]

def test_non_critical_event_logging(audit_logger, temp_log_file):
    # Log a non-critical event
    audit_logger.log_auth_event(
        SecurityEventType.LOGIN_SUCCESS,
        "test_user",
        "127.0.0.1"
    )
    
    # Read log file
    with open(temp_log_file, 'r') as f:
        log_lines = f.readlines()
        
    # Should only have INFO log
    assert len(log_lines) == 1
    assert "INFO" in log_lines[0]

def test_event_id_uniqueness():
    # Create multiple events with same data
    events = [
        SecurityEvent(
            timestamp=datetime.utcnow(),
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id="test_user",
            service_id=None,
            ip_address="127.0.0.1",
            details={}
        )
        for _ in range(3)
    ]
    
    # Event IDs should be unique due to timestamp
    event_ids = {event.event_id for event in events}
    assert len(event_ids) == 3 