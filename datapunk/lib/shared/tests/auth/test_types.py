import pytest
from datetime import datetime
from typing import Dict, Any, Optional, Union

from datapunk_shared.auth.types import (
    TPolicy,
    TUser,
    Metadata,
    Timestamp,
    ResourceID,
    UserID,
    AuthToken,
    AuthContext,
    AuthResult,
    ValidationContext,
    ValidationResult,
    PolicyContext,
    PolicyResult,
    AuditContext,
    AuditResult,
    Result
)

class TestAuthTypes:
    def test_metadata_type(self):
        """Test Metadata type annotation."""
        metadata: Metadata = {
            "key1": "value1",
            "key2": 123,
            "key3": {"nested": True}
        }
        assert isinstance(metadata, dict)
        assert all(isinstance(k, str) for k in metadata.keys())

    def test_timestamp_type(self):
        """Test Timestamp type annotation."""
        timestamp: Timestamp = datetime.utcnow()
        assert isinstance(timestamp, datetime)

    def test_resource_id_type(self):
        """Test ResourceID type annotation."""
        resource_id: ResourceID = "resource_123"
        assert isinstance(resource_id, str)

    def test_user_id_type(self):
        """Test UserID type annotation."""
        user_id: UserID = "user_123"
        assert isinstance(user_id, str)

    def test_auth_token_type(self):
        """Test AuthToken type annotation."""
        token: AuthToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert isinstance(token, str)

    def test_auth_context_type(self):
        """Test AuthContext type annotation."""
        context: AuthContext = {
            "headers": {"Authorization": "Bearer token"},
            "claims": {"sub": "user_123", "scope": ["read", "write"]},
            "ip_address": "127.0.0.1"
        }
        assert isinstance(context, dict)
        assert all(isinstance(k, str) for k in context.keys())

    def test_auth_result_type(self):
        """Test AuthResult type annotation."""
        result: AuthResult = {
            "success": True,
            "token": "new_token",
            "expires_at": datetime.utcnow().isoformat()
        }
        assert isinstance(result, dict)
        assert all(isinstance(k, str) for k in result.keys())

    def test_validation_context_type(self):
        """Test ValidationContext type annotation."""
        context: ValidationContext = {
            "input": {"field1": "value1"},
            "rules": {"field1": "required|string"}
        }
        assert isinstance(context, dict)
        assert all(isinstance(k, str) for k in context.keys())

    def test_validation_result_type(self):
        """Test ValidationResult type annotation."""
        result: ValidationResult = {
            "field1": True,
            "field2": False
        }
        assert isinstance(result, dict)
        assert all(isinstance(k, str) for k in result.keys())
        assert all(isinstance(v, bool) for v in result.values())

    def test_policy_context_type(self):
        """Test PolicyContext type annotation."""
        context: PolicyContext = {
            "user": {"id": "user_123", "roles": ["admin"]},
            "resource": "resource_123",
            "action": "read"
        }
        assert isinstance(context, dict)
        assert all(isinstance(k, str) for k in context.keys())

    def test_policy_result_type(self):
        """Test PolicyResult type annotation."""
        result: PolicyResult = {
            "allowed": True,
            "reason": "User has required role",
            "applied_rules": ["role_check", "resource_access"]
        }
        assert isinstance(result, dict)
        assert all(isinstance(k, str) for k in result.keys())

    def test_audit_context_type(self):
        """Test AuditContext type annotation."""
        context: AuditContext = {
            "user_id": "user_123",
            "action": "resource_access",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"ip": "127.0.0.1"}
        }
        assert isinstance(context, dict)
        assert all(isinstance(k, str) for k in context.keys())

    def test_audit_result_type(self):
        """Test AuditResult type annotation."""
        result: AuditResult = {
            "success": True,
            "log_id": "audit_123",
            "stored_at": datetime.utcnow().isoformat()
        }
        assert isinstance(result, dict)
        assert all(isinstance(k, str) for k in result.keys())

    def test_result_type(self):
        """Test Result type annotation."""
        result: Result = {
            "success": True,
            "message": "Operation completed",
            "data": {
                "id": "123",
                "status": "completed"
            }
        }
        assert isinstance(result, dict)
        assert isinstance(result.get("success"), bool)
        assert all(isinstance(k, str) for k in result.keys())

    def test_generic_policy_type(self):
        """Test TPolicy generic type variable."""
        class CustomPolicy:
            pass
        
        policy: TPolicy = CustomPolicy()
        assert isinstance(policy, CustomPolicy)

    def test_generic_user_type(self):
        """Test TUser generic type variable."""
        class CustomUser:
            pass
        
        user: TUser = CustomUser()
        assert isinstance(user, CustomUser) 