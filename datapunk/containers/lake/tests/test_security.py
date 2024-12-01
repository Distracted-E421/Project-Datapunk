import unittest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime, timedelta
import time

from ..src.storage.index.security import (
    SecurityManager,
    Permission,
    AuditAction,
    Role,
    User
)

class TestSecuritySystem(unittest.TestCase):
    def setUp(self):
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "security_config.json"
        self.audit_dir = Path(self.temp_dir) / "audit"
        
        # Create test configuration
        config = {
            "audit": {
                "enabled": True,
                "retention_days": 7,
                "log_rotation_size_mb": 10
            },
            "authentication": {
                "api_key_expiry_days": 30,
                "max_failed_attempts": 3,
                "lockout_duration_minutes": 15
            },
            "encryption": {
                "enabled": True,
                "algorithm": "AES-256-GCM",
                "master_key": "test-master-key",
                "key_rotation_days": 7
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
            
        # Initialize security manager
        self.security = SecurityManager(
            self.config_path,
            self.audit_dir
        )
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_role_creation(self):
        """Test role creation and permissions."""
        # Create custom role
        self.security.create_role(
            "custom_role",
            {Permission.READ, Permission.WRITE},
            {"test_index", "other_index"}
        )
        
        # Verify role exists
        self.assertIn("custom_role", self.security.roles)
        role = self.security.roles["custom_role"]
        
        self.assertEqual(role.name, "custom_role")
        self.assertEqual(
            role.permissions,
            {Permission.READ, Permission.WRITE}
        )
        self.assertEqual(
            role.indexes,
            {"test_index", "other_index"}
        )
        
    def test_user_creation(self):
        """Test user creation and API key generation."""
        # Create user
        api_key = self.security.create_user(
            "test_user",
            {"reader"}
        )
        
        # Verify user exists
        self.assertIn("test_user", self.security.users)
        user = self.security.users["test_user"]
        
        self.assertEqual(user.user_id, "test_user")
        self.assertEqual(user.roles, {"reader"})
        self.assertIsNotNone(api_key)
        
    def test_authentication(self):
        """Test user authentication."""
        # Create user and get API key
        api_key = self.security.create_user(
            "auth_test",
            {"reader"}
        )
        
        # Test valid authentication
        user_id = self.security.authenticate(api_key)
        self.assertEqual(user_id, "auth_test")
        
        # Test invalid authentication
        invalid_user = self.security.authenticate("invalid-key")
        self.assertIsNone(invalid_user)
        
    def test_permission_checking(self):
        """Test permission checking."""
        # Create role with specific permissions
        self.security.create_role(
            "test_role",
            {Permission.READ},
            {"test_index"}
        )
        
        # Create user with role
        api_key = self.security.create_user(
            "perm_test",
            {"test_role"}
        )
        
        # Test allowed permission
        self.assertTrue(
            self.security.check_permission(
                "perm_test",
                Permission.READ,
                "test_index"
            )
        )
        
        # Test denied permission
        self.assertFalse(
            self.security.check_permission(
                "perm_test",
                Permission.WRITE,
                "test_index"
            )
        )
        
        # Test denied index
        self.assertFalse(
            self.security.check_permission(
                "perm_test",
                Permission.READ,
                "other_index"
            )
        )
        
    def test_audit_logging(self):
        """Test audit logging."""
        # Create test action
        self.security.audit_log(
            AuditAction.INDEX_CREATE,
            "test_index",
            {"details": "test creation"},
            "success",
            "127.0.0.1"
        )
        
        # Verify log file exists
        log_file = list(self.audit_dir.glob("audit_*.log"))[0]
        self.assertTrue(log_file.exists())
        
        # Read log entry
        with open(log_file, 'r') as f:
            log_entry = json.loads(f.readline())
            
        self.assertEqual(log_entry["action"], "index_create")
        self.assertEqual(log_entry["index_name"], "test_index")
        self.assertEqual(log_entry["status"], "success")
        self.assertEqual(log_entry["client_ip"], "127.0.0.1")
        
    def test_encryption(self):
        """Test data encryption and decryption."""
        # Test data
        test_data = b"sensitive data"
        
        # Encrypt data
        encrypted = self.security.encrypt_data(test_data)
        self.assertNotEqual(encrypted, test_data)
        
        # Decrypt data
        decrypted = self.security.decrypt_data(encrypted)
        self.assertEqual(decrypted, test_data)
        
    def test_key_rotation(self):
        """Test encryption key rotation."""
        # Encrypt data with original key
        test_data = b"test data"
        encrypted = self.security.encrypt_data(test_data)
        
        # Store original key
        original_key = self.security.encryption_key
        
        # Rotate key
        self.security.rotate_encryption_key()
        
        # Verify key changed
        self.assertNotEqual(
            self.security.encryption_key,
            original_key
        )
        
    def test_admin_permissions(self):
        """Test admin role permissions."""
        # Get admin API key
        admin = self.security.users["admin"]
        
        # Verify admin has all permissions
        for permission in Permission:
            self.assertTrue(
                self.security.check_permission(
                    "admin",
                    permission,
                    "any_index"
                )
            )
            
    def test_wildcard_index_permission(self):
        """Test wildcard index permissions."""
        # Create role with wildcard index
        self.security.create_role(
            "wildcard_role",
            {Permission.READ},
            {"*"}
        )
        
        # Create user
        self.security.create_user(
            "wildcard_user",
            {"wildcard_role"}
        )
        
        # Test permission on various indexes
        self.assertTrue(
            self.security.check_permission(
                "wildcard_user",
                Permission.READ,
                "any_index"
            )
        )
        
        self.assertTrue(
            self.security.check_permission(
                "wildcard_user",
                Permission.READ,
                "another_index"
            )
        )
        
    def test_multiple_roles(self):
        """Test user with multiple roles."""
        # Create roles
        self.security.create_role(
            "role1",
            {Permission.READ},
            {"index1"}
        )
        
        self.security.create_role(
            "role2",
            {Permission.WRITE},
            {"index2"}
        )
        
        # Create user with both roles
        self.security.create_user(
            "multi_role_user",
            {"role1", "role2"}
        )
        
        # Test permissions from both roles
        self.assertTrue(
            self.security.check_permission(
                "multi_role_user",
                Permission.READ,
                "index1"
            )
        )
        
        self.assertTrue(
            self.security.check_permission(
                "multi_role_user",
                Permission.WRITE,
                "index2"
            )
        )
        
        # Test permission combinations
        self.assertFalse(
            self.security.check_permission(
                "multi_role_user",
                Permission.WRITE,
                "index1"
            )
        )
        
        self.assertFalse(
            self.security.check_permission(
                "multi_role_user",
                Permission.READ,
                "index2"
            )
        )