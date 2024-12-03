import unittest
from datetime import datetime, timedelta
from src.infrastructure.security_manager import (
    SecurityManager,
    SecurityPolicy,
    SecurityLevel,
    ResourceType,
    SecurityEvent
)

class TestSecurityManager(unittest.TestCase):
    def setUp(self):
        self.manager = SecurityManager()
        self.test_policy = SecurityPolicy(
            name="test_policy",
            level=SecurityLevel.HIGH,
            resource_types={ResourceType.API, ResourceType.DATABASE},
            require_mfa=True
        )

    def test_policy_management(self):
        """Test security policy management."""
        self.manager.add_policy(self.test_policy)
        
        # Test policy application
        result = self.manager.validate_access(
            ResourceType.API,
            user_id="test_user",
            source_ip="127.0.0.1",
            security_level=SecurityLevel.HIGH
        )
        self.assertTrue(result)  # Should pass as MFA verification is mocked

    def test_token_management(self):
        """Test JWT token generation and validation."""
        # Generate token
        token = self.manager.generate_token(
            user_id="test_user",
            additional_claims={'role': 'admin'}
        )
        
        # Validate token
        claims = self.manager.validate_token(token)
        self.assertIsNotNone(claims)
        self.assertEqual(claims['user_id'], "test_user")
        self.assertEqual(claims['role'], "admin")
        
        # Test invalid token
        invalid_claims = self.manager.validate_token("invalid.token.here")
        self.assertIsNone(invalid_claims)

    def test_encryption(self):
        """Test data encryption and decryption."""
        original_data = "sensitive information"
        
        # Encrypt data
        encrypted = self.manager.encrypt_data(original_data)
        self.assertNotEqual(encrypted, original_data)
        
        # Decrypt data
        decrypted = self.manager.decrypt_data(encrypted)
        self.assertEqual(decrypted, original_data)
        
        # Test invalid data
        with self.assertRaises(Exception):
            self.manager.decrypt_data("invalid_encrypted_data")

    def test_ip_blocking(self):
        """Test IP blocking functionality."""
        test_ip = "192.168.1.1"
        
        # Record multiple failed attempts
        for _ in range(self.manager.default_policy.max_attempts):
            self.manager._record_failed_attempt(test_ip)
        
        # Verify IP is blocked
        self.assertTrue(self.manager._is_ip_blocked(test_ip))
        
        # Test block expiration
        self.manager.blocked_ips[test_ip] = datetime.now() - timedelta(
            seconds=self.manager.default_policy.lockout_duration + 1
        )
        self.assertFalse(self.manager._is_ip_blocked(test_ip))

    def test_security_events(self):
        """Test security event logging and analysis."""
        # Create test events
        events = [
            SecurityEvent(
                timestamp=datetime.now(),
                event_type="login_attempt",
                resource_type=ResourceType.API,
                severity=SecurityLevel.MEDIUM,
                description="Failed login attempt",
                source_ip="192.168.1.1"
            ),
            SecurityEvent(
                timestamp=datetime.now(),
                event_type="unauthorized_access",
                resource_type=ResourceType.DATABASE,
                severity=SecurityLevel.HIGH,
                description="Unauthorized database access",
                source_ip="192.168.1.1"
            )
        ]
        
        # Log events
        for event in events:
            self.manager._log_security_event(event)
        
        # Test event retrieval
        filtered_events = self.manager.get_security_events(
            min_severity=SecurityLevel.HIGH
        )
        self.assertEqual(len(filtered_events), 1)
        
        # Test pattern analysis
        analysis = self.manager.analyze_security_patterns()
        self.assertEqual(analysis['total_events'], 2)
        self.assertEqual(len(analysis['events_by_type']), 2)
        self.assertIn('192.168.1.1', analysis['top_source_ips'])

    def test_policy_inheritance(self):
        """Test security policy inheritance and override."""
        # Create policies with different levels
        low_policy = SecurityPolicy(
            name="low_policy",
            level=SecurityLevel.LOW,
            resource_types={ResourceType.API}
        )
        high_policy = SecurityPolicy(
            name="high_policy",
            level=SecurityLevel.HIGH,
            resource_types={ResourceType.API}
        )
        
        self.manager.add_policy(low_policy)
        self.manager.add_policy(high_policy)
        
        # Test policy selection
        selected_policy = self.manager._get_applicable_policy(
            ResourceType.API,
            SecurityLevel.HIGH
        )
        self.assertEqual(selected_policy.level, SecurityLevel.HIGH)

    def test_mfa_requirement(self):
        """Test MFA requirement enforcement."""
        # Create policy requiring MFA
        mfa_policy = SecurityPolicy(
            name="mfa_policy",
            level=SecurityLevel.HIGH,
            resource_types={ResourceType.DATABASE},
            require_mfa=True
        )
        self.manager.add_policy(mfa_policy)
        
        # Test access with MFA requirement
        result = self.manager.validate_access(
            ResourceType.DATABASE,
            user_id="test_user",
            source_ip="127.0.0.1"
        )
        self.assertTrue(result)  # Should pass as MFA verification is mocked

    def test_security_event_filtering(self):
        """Test security event filtering capabilities."""
        # Create events at different times and severities
        now = datetime.now()
        events = [
            SecurityEvent(
                timestamp=now - timedelta(hours=2),
                event_type="test",
                resource_type=ResourceType.API,
                severity=SecurityLevel.LOW,
                description="Old low severity event"
            ),
            SecurityEvent(
                timestamp=now - timedelta(hours=1),
                event_type="test",
                resource_type=ResourceType.API,
                severity=SecurityLevel.HIGH,
                description="Old high severity event"
            ),
            SecurityEvent(
                timestamp=now,
                event_type="test",
                resource_type=ResourceType.API,
                severity=SecurityLevel.CRITICAL,
                description="Recent critical event"
            )
        ]
        
        for event in events:
            self.manager._log_security_event(event)
        
        # Test time-based filtering
        recent_events = self.manager.get_security_events(
            start_time=now - timedelta(hours=1)
        )
        self.assertEqual(len(recent_events), 2)
        
        # Test severity-based filtering
        high_severity_events = self.manager.get_security_events(
            min_severity=SecurityLevel.HIGH
        )
        self.assertEqual(len(high_severity_events), 2)
        
        # Test combined filtering
        filtered_events = self.manager.get_security_events(
            start_time=now - timedelta(hours=1),
            min_severity=SecurityLevel.CRITICAL
        )
        self.assertEqual(len(filtered_events), 1)

if __name__ == '__main__':
    unittest.main() 