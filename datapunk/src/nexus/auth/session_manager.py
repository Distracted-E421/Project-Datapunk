from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, Set, List
import hashlib
import json
import re
import user_agents

@dataclass
class DeviceFingerprint:
    user_agent: str
    os_family: str
    os_version: str
    browser_family: str
    browser_version: str
    device_family: str
    is_mobile: bool
    is_tablet: bool
    is_bot: bool
    screen_resolution: Optional[str] = None
    color_depth: Optional[int] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    canvas_hash: Optional[str] = None  # Hash of canvas fingerprint
    webgl_hash: Optional[str] = None   # Hash of WebGL fingerprint
    
    def calculate_hash(self) -> str:
        """Calculate a unique hash for this device fingerprint."""
        data = {
            "ua": self.user_agent,
            "os": f"{self.os_family}/{self.os_version}",
            "browser": f"{self.browser_family}/{self.browser_version}",
            "device": self.device_family,
            "screen": self.screen_resolution,
            "color": self.color_depth,
            "tz": self.timezone,
            "lang": self.language,
            "canvas": self.canvas_hash,
            "webgl": self.webgl_hash
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

@dataclass
class Session:
    session_id: str
    user_id: str
    device_fingerprint: DeviceFingerprint
    ip_address: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))
    is_mfa_complete: bool = False
    is_suspicious: bool = False
    risk_score: float = 0.0
    location_info: Optional[Dict] = None

class SessionManager:
    def __init__(self, max_sessions_per_user: int = 5,
                 session_lifetime: timedelta = timedelta(hours=24),
                 suspicious_threshold: float = 0.7):
        self._sessions: Dict[str, Session] = {}
        self._user_sessions: Dict[str, Set[str]] = {}
        self._device_history: Dict[str, Dict[str, Set[str]]] = {}  # user_id -> fingerprint -> session_ids
        self.max_sessions_per_user = max_sessions_per_user
        self.session_lifetime = session_lifetime
        self.suspicious_threshold = suspicious_threshold
        
    def create_fingerprint(self, user_agent_string: str, **additional_data) -> DeviceFingerprint:
        """Create a device fingerprint from user agent and additional data."""
        ua = user_agents.parse(user_agent_string)
        
        return DeviceFingerprint(
            user_agent=user_agent_string,
            os_family=ua.os.family,
            os_version=ua.os.version_string,
            browser_family=ua.browser.family,
            browser_version=ua.browser.version_string,
            device_family=ua.device.family,
            is_mobile=ua.is_mobile,
            is_tablet=ua.is_tablet,
            is_bot=ua.is_bot,
            screen_resolution=additional_data.get("screen_resolution"),
            color_depth=additional_data.get("color_depth"),
            timezone=additional_data.get("timezone"),
            language=additional_data.get("language"),
            canvas_hash=additional_data.get("canvas_hash"),
            webgl_hash=additional_data.get("webgl_hash")
        )
        
    def create_session(self, user_id: str, device_fingerprint: DeviceFingerprint,
                      ip_address: str, location_info: Optional[Dict] = None) -> Session:
        """Create a new session with risk assessment."""
        # Generate session ID
        session_id = hashlib.sha256(
            f"{user_id}:{datetime.utcnow().isoformat()}:{device_fingerprint.calculate_hash()}".encode()
        ).hexdigest()
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(user_id, device_fingerprint, ip_address)
        
        # Create session
        session = Session(
            session_id=session_id,
            user_id=user_id,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            expires_at=datetime.utcnow() + self.session_lifetime,
            is_suspicious=risk_score > self.suspicious_threshold,
            risk_score=risk_score,
            location_info=location_info
        )
        
        # Store session
        self._sessions[session_id] = session
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = set()
        self._user_sessions[user_id].add(session_id)
        
        # Update device history
        fingerprint_hash = device_fingerprint.calculate_hash()
        if user_id not in self._device_history:
            self._device_history[user_id] = {}
        if fingerprint_hash not in self._device_history[user_id]:
            self._device_history[user_id][fingerprint_hash] = set()
        self._device_history[user_id][fingerprint_hash].add(session_id)
        
        # Enforce session limit
        self._enforce_session_limit(user_id)
        
        return session
        
    def _calculate_risk_score(self, user_id: str, device_fingerprint: DeviceFingerprint,
                            ip_address: str) -> float:
        """Calculate risk score for new session."""
        risk_factors = []
        
        # Check if device is known
        fingerprint_hash = device_fingerprint.calculate_hash()
        is_known_device = (
            user_id in self._device_history and
            fingerprint_hash in self._device_history[user_id]
        )
        risk_factors.append(0.0 if is_known_device else 0.5)
        
        # Check if bot
        if device_fingerprint.is_bot:
            risk_factors.append(1.0)
            
        # Check for suspicious user agent patterns
        suspicious_patterns = [
            r"(?i)curl",
            r"(?i)python",
            r"(?i)wget",
            r"(?i)phantom",
            r"(?i)selenium"
        ]
        if any(re.search(pattern, device_fingerprint.user_agent) for pattern in suspicious_patterns):
            risk_factors.append(0.8)
            
        # Calculate final score (average of risk factors)
        return sum(risk_factors) / len(risk_factors) if risk_factors else 0.0
        
    def _enforce_session_limit(self, user_id: str):
        """Enforce maximum sessions per user by removing oldest sessions."""
        if user_id not in self._user_sessions:
            return
            
        user_session_ids = self._user_sessions[user_id]
        if len(user_session_ids) <= self.max_sessions_per_user:
            return
            
        # Sort sessions by last active time
        sessions = [(sid, self._sessions[sid]) for sid in user_session_ids]
        sessions.sort(key=lambda x: x[1].last_active)
        
        # Remove oldest sessions
        for session_id, _ in sessions[:-self.max_sessions_per_user]:
            self.end_session(session_id)
            
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID and update last active time."""
        session = self._sessions.get(session_id)
        if not session:
            return None
            
        # Check if session has expired
        if datetime.utcnow() > session.expires_at:
            self.end_session(session_id)
            return None
            
        # Update last active time
        session.last_active = datetime.utcnow()
        return session
        
    def end_session(self, session_id: str):
        """End a session."""
        if session_id not in self._sessions:
            return
            
        session = self._sessions[session_id]
        
        # Remove from user sessions
        if session.user_id in self._user_sessions:
            self._user_sessions[session.user_id].discard(session_id)
            
        # Remove from device history
        fingerprint_hash = session.device_fingerprint.calculate_hash()
        if (session.user_id in self._device_history and
            fingerprint_hash in self._device_history[session.user_id]):
            self._device_history[session.user_id][fingerprint_hash].discard(session_id)
            
        # Remove session
        del self._sessions[session_id]
        
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user."""
        if user_id not in self._user_sessions:
            return []
            
        sessions = []
        for session_id in list(self._user_sessions[user_id]):
            session = self.get_session(session_id)  # This will handle expired sessions
            if session:
                sessions.append(session)
                
        return sessions
        
    def is_known_device(self, user_id: str, device_fingerprint: DeviceFingerprint) -> bool:
        """Check if device is known for user."""
        fingerprint_hash = device_fingerprint.calculate_hash()
        return (
            user_id in self._device_history and
            fingerprint_hash in self._device_history[user_id] and
            self._device_history[user_id][fingerprint_hash]
        ) 