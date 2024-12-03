import pytest
from datetime import datetime, timedelta
from src.nexus.auth.session_manager import (
    SessionManager,
    DeviceFingerprint,
    Session
)

@pytest.fixture
def session_manager():
    return SessionManager(
        max_sessions_per_user=3,
        session_lifetime=timedelta(hours=1),
        suspicious_threshold=0.7
    )

@pytest.fixture
def device_fingerprint():
    return DeviceFingerprint(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
        os_family="Windows",
        os_version="10",
        browser_family="Chrome",
        browser_version="91.0.4472.124",
        device_family="Other",
        is_mobile=False,
        is_tablet=False,
        is_bot=False,
        screen_resolution="1920x1080",
        color_depth=24,
        timezone="UTC",
        language="en-US",
        canvas_hash="canvas_hash_123",
        webgl_hash="webgl_hash_456"
    )

def test_device_fingerprint_creation(session_manager):
    fingerprint = session_manager.create_fingerprint(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
        screen_resolution="1920x1080",
        color_depth=24,
        timezone="UTC",
        language="en-US"
    )
    
    assert fingerprint.os_family == "Windows"
    assert fingerprint.browser_family == "Chrome"
    assert fingerprint.is_mobile is False
    assert fingerprint.is_bot is False
    assert fingerprint.screen_resolution == "1920x1080"

def test_session_creation(session_manager, device_fingerprint):
    user_id = "test_user"
    ip_address = "192.168.1.1"
    
    session = session_manager.create_session(
        user_id,
        device_fingerprint,
        ip_address
    )
    
    assert session.user_id == user_id
    assert session.ip_address == ip_address
    assert session.device_fingerprint == device_fingerprint
    assert session.is_suspicious is False
    assert session.risk_score < session_manager.suspicious_threshold

def test_session_retrieval(session_manager, device_fingerprint):
    user_id = "test_user"
    session = session_manager.create_session(
        user_id,
        device_fingerprint,
        "192.168.1.1"
    )
    
    # Retrieve session
    retrieved = session_manager.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    assert retrieved.user_id == user_id
    
    # Try retrieving non-existent session
    assert session_manager.get_session("nonexistent") is None

def test_session_expiry(session_manager, device_fingerprint):
    session_manager.session_lifetime = timedelta(seconds=1)
    
    session = session_manager.create_session(
        "test_user",
        device_fingerprint,
        "192.168.1.1"
    )
    
    # Session should be valid initially
    assert session_manager.get_session(session.session_id) is not None
    
    # Wait for session to expire
    session.expires_at = datetime.utcnow() - timedelta(seconds=1)
    
    # Session should be expired
    assert session_manager.get_session(session.session_id) is None

def test_session_limit(session_manager, device_fingerprint):
    user_id = "test_user"
    
    # Create maximum allowed sessions
    sessions = []
    for i in range(session_manager.max_sessions_per_user + 1):
        session = session_manager.create_session(
            user_id,
            device_fingerprint,
            f"192.168.1.{i}"
        )
        sessions.append(session)
        
    # Verify oldest session was removed
    assert len(session_manager.get_user_sessions(user_id)) == session_manager.max_sessions_per_user
    assert session_manager.get_session(sessions[0].session_id) is None

def test_device_recognition(session_manager, device_fingerprint):
    user_id = "test_user"
    
    # Create session with device
    session_manager.create_session(
        user_id,
        device_fingerprint,
        "192.168.1.1"
    )
    
    # Check if device is recognized
    assert session_manager.is_known_device(user_id, device_fingerprint) is True
    
    # Check unknown device
    new_fingerprint = DeviceFingerprint(
        user_agent="Different User Agent",
        os_family="Linux",
        os_version="20.04",
        browser_family="Firefox",
        browser_version="89.0",
        device_family="Other",
        is_mobile=False,
        is_tablet=False,
        is_bot=False
    )
    assert session_manager.is_known_device(user_id, new_fingerprint) is False

def test_risk_assessment(session_manager):
    # Test bot detection
    bot_fingerprint = DeviceFingerprint(
        user_agent="Googlebot/2.1",
        os_family="",
        os_version="",
        browser_family="",
        browser_version="",
        device_family="Spider",
        is_mobile=False,
        is_tablet=False,
        is_bot=True
    )
    
    session = session_manager.create_session(
        "test_user",
        bot_fingerprint,
        "192.168.1.1"
    )
    assert session.is_suspicious is True
    assert session.risk_score > session_manager.suspicious_threshold
    
    # Test suspicious user agent
    suspicious_fingerprint = DeviceFingerprint(
        user_agent="curl/7.64.1",
        os_family="",
        os_version="",
        browser_family="",
        browser_version="",
        device_family="Other",
        is_mobile=False,
        is_tablet=False,
        is_bot=False
    )
    
    session = session_manager.create_session(
        "test_user",
        suspicious_fingerprint,
        "192.168.1.1"
    )
    assert session.risk_score > 0.5

def test_session_cleanup(session_manager, device_fingerprint):
    user_id = "test_user"
    
    # Create expired session
    session = session_manager.create_session(
        user_id,
        device_fingerprint,
        "192.168.1.1"
    )
    session.expires_at = datetime.utcnow() - timedelta(hours=1)
    
    # Create active session
    active_session = session_manager.create_session(
        user_id,
        device_fingerprint,
        "192.168.1.2"
    )
    
    # Get user sessions should only return active session
    user_sessions = session_manager.get_user_sessions(user_id)
    assert len(user_sessions) == 1
    assert user_sessions[0].session_id == active_session.session_id

def test_concurrent_sessions(session_manager, device_fingerprint):
    user_id = "test_user"
    
    # Create sessions from different locations
    session1 = session_manager.create_session(
        user_id,
        device_fingerprint,
        "192.168.1.1",
        location_info={"country": "US", "city": "New York"}
    )
    
    session2 = session_manager.create_session(
        user_id,
        device_fingerprint,
        "192.168.1.2",
        location_info={"country": "FR", "city": "Paris"}
    )
    
    # Both sessions should exist but have higher risk scores
    assert session_manager.get_session(session1.session_id) is not None
    assert session_manager.get_session(session2.session_id) is not None
    assert session2.risk_score > session1.risk_score 