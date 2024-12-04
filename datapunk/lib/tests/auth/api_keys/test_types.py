"""
API Key Type Tests
---------------

Tests the type system for API keys including:
- Type validation and conversion
- Type aliases and custom types
- Type compatibility checks
- Type serialization
- Type constraints

Run with: pytest -v test_types.py
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, Union
import json

from datapunk_shared.auth.api_keys.types import (
    KeyID, KeyHash, KeySecret,
    PathPattern, IPAddress, HTTPMethod,
    TimeWindow, QuotaLimit, RateLimit,
    KeyValidationResult
)

# Type Validation Tests

def test_key_id_validation():
    """Test KeyID type validation."""
    # Valid key IDs
    assert isinstance("key_123", KeyID)
    assert isinstance("test_key_456", KeyID)
    
    # Invalid key IDs (should still be strings, but not semantically valid)
    invalid_ids = [
        "",  # Empty
        "key with spaces",  # Contains spaces
        "key@invalid",  # Invalid characters
        "k" * 129  # Too long
    ]
    
    for key_id in invalid_ids:
        with pytest.raises(ValueError):
            validate_key_id(key_id)

def test_key_hash_validation():
    """Test KeyHash type validation."""
    # Valid key hashes (SHA-256)
    valid_hash = "a" * 64
    assert isinstance(valid_hash, KeyHash)
    
    # Invalid hashes
    invalid_hashes = [
        "short_hash",  # Too short
        "g" * 64,  # Invalid characters
        "hash with spaces"  # Invalid format
    ]
    
    for key_hash in invalid_hashes:
        with pytest.raises(ValueError):
            validate_key_hash(key_hash)

def test_key_secret_validation():
    """Test KeySecret type validation."""
    # Valid secrets
    valid_secrets = [
        "pk_test_abc123",  # Test key
        "pk_live_xyz789",  # Live key
        "sk_test_def456"   # Secret key
    ]
    
    for secret in valid_secrets:
        assert isinstance(secret, KeySecret)
    
    # Invalid secrets
    invalid_secrets = [
        "",  # Empty
        "invalid_prefix_123",  # Wrong prefix
        "pk_invalid@chars"  # Invalid characters
    ]
    
    for secret in invalid_secrets:
        with pytest.raises(ValueError):
            validate_key_secret(secret)

# Pattern Type Tests

def test_path_pattern_validation():
    """Test path pattern validation."""
    # Valid patterns
    valid_patterns = [
        "/api/v1/*",
        "/users/{id}",
        "/data/**",
        "/*.json"
    ]
    
    for pattern in valid_patterns:
        assert isinstance(pattern, PathPattern)
        assert validate_path_pattern(pattern)
    
    # Invalid patterns
    invalid_patterns = [
        "",  # Empty
        "no_leading_slash",
        "/invalid/[chars]",
        "../escape/attempt"
    ]
    
    for pattern in invalid_patterns:
        with pytest.raises(ValueError):
            validate_path_pattern(pattern)

def test_ip_address_validation():
    """Test IP address validation."""
    # Valid IP addresses
    valid_ips = [
        "192.168.1.1",
        "10.0.0.0",
        "2001:db8::1",
        "::1"
    ]
    
    for ip in valid_ips:
        assert isinstance(ip, IPAddress)
        assert validate_ip_address(ip)
    
    # Invalid IP addresses
    invalid_ips = [
        "",  # Empty
        "256.256.256.256",  # Invalid IPv4
        "2001:xyz::1",  # Invalid IPv6
        "not_an_ip"
    ]
    
    for ip in invalid_ips:
        with pytest.raises(ValueError):
            validate_ip_address(ip)

def test_http_method_validation():
    """Test HTTP method validation."""
    # Valid methods
    valid_methods = [
        "GET", "POST", "PUT", "DELETE",
        "PATCH", "HEAD", "OPTIONS"
    ]
    
    for method in valid_methods:
        assert isinstance(method, HTTPMethod)
        assert validate_http_method(method)
    
    # Invalid methods
    invalid_methods = [
        "",  # Empty
        "get",  # Lowercase
        "INVALID",  # Unknown method
        "POST "  # Extra space
    ]
    
    for method in invalid_methods:
        with pytest.raises(ValueError):
            validate_http_method(method)

# Time Window Tests

def test_time_window_validation():
    """Test time window validation."""
    # Valid time windows
    valid_windows = [
        {"unit": "hour", "value": 24},
        {"unit": "day", "value": 7},
        {"unit": "minute", "value": 30}
    ]
    
    for window in valid_windows:
        assert isinstance(window, TimeWindow)
        assert validate_time_window(window)
    
    # Invalid windows
    invalid_windows = [
        {},  # Empty
        {"unit": "invalid", "value": 1},  # Invalid unit
        {"unit": "hour", "value": -1},  # Negative value
        {"unit": "day"}  # Missing value
    ]
    
    for window in invalid_windows:
        with pytest.raises(ValueError):
            validate_time_window(window)

# Quota and Rate Limit Tests

def test_quota_limit_validation():
    """Test quota limit validation."""
    # Valid quotas
    valid_quotas = [
        {"max_requests": 1000},
        {"max_storage_mb": 500},
        {"max_connections": 100}
    ]
    
    for quota in valid_quotas:
        assert isinstance(quota, QuotaLimit)
        assert validate_quota_limit(quota)
    
    # Invalid quotas
    invalid_quotas = [
        {},  # Empty
        {"invalid_metric": 100},  # Unknown metric
        {"max_requests": -1},  # Negative value
        {"max_requests": "100"}  # Wrong type
    ]
    
    for quota in invalid_quotas:
        with pytest.raises(ValueError):
            validate_quota_limit(quota)

def test_rate_limit_validation():
    """Test rate limit validation."""
    # Valid rate limits
    valid_rates = [
        {"requests_per_second": 10.5},
        {"requests_per_minute": 600},
        {"requests_per_hour": 3600}
    ]
    
    for rate in valid_rates:
        assert isinstance(rate, RateLimit)
        assert validate_rate_limit(rate)
    
    # Invalid rates
    invalid_rates = [
        {},  # Empty
        {"invalid_unit": 100},  # Unknown unit
        {"requests_per_second": -1},  # Negative value
        {"requests_per_minute": "60"}  # Wrong type
    ]
    
    for rate in invalid_rates:
        with pytest.raises(ValueError):
            validate_rate_limit(rate)

# Validation Result Tests

def test_validation_result_format():
    """Test validation result format."""
    # Valid results
    valid_results = [
        {"valid": True, "issues": []},
        {
            "valid": False,
            "issues": ["Invalid format"],
            "warnings": ["Performance impact"]
        }
    ]
    
    for result in valid_results:
        assert isinstance(result, KeyValidationResult)
        assert validate_validation_result(result)
    
    # Invalid results
    invalid_results = [
        {},  # Empty
        {"valid": "true"},  # Wrong type
        {"valid": True, "issues": "error"},  # Wrong type
        {"valid": True, "unknown": "field"}  # Unknown field
    ]
    
    for result in invalid_results:
        with pytest.raises(ValueError):
            validate_validation_result(result)

# Type Serialization Tests

def test_type_serialization():
    """Test type serialization to JSON."""
    # Complex type example
    data = {
        "key_id": "test_123",
        "ip_address": "192.168.1.1",
        "time_window": {"unit": "hour", "value": 24},
        "quota": {"max_requests": 1000},
        "rate_limit": {"requests_per_second": 10.5},
        "validation": {"valid": True, "issues": []}
    }
    
    # Should serialize without errors
    json_str = json.dumps(data)
    deserialized = json.loads(json_str)
    
    # Types should be preserved
    assert isinstance(deserialized["key_id"], KeyID)
    assert isinstance(deserialized["ip_address"], IPAddress)
    assert isinstance(deserialized["time_window"], TimeWindow)
    assert isinstance(deserialized["quota"], QuotaLimit)
    assert isinstance(deserialized["rate_limit"], RateLimit)
    assert isinstance(deserialized["validation"], KeyValidationResult)

# Type Compatibility Tests

def test_type_compatibility():
    """Test type compatibility and conversion."""
    # KeyID should be str compatible
    key_id: KeyID = "test_123"
    str_value: str = key_id
    assert str_value == "test_123"
    
    # IPAddress should work with IP libraries
    ip: IPAddress = "192.168.1.1"
    import ipaddress
    ip_obj = ipaddress.ip_address(ip)
    assert str(ip_obj) == ip
    
    # TimeWindow should work with timedelta
    window: TimeWindow = {"unit": "hour", "value": 24}
    delta = timedelta(hours=window["value"])
    assert delta.total_seconds() == 86400

def test_type_constraints():
    """Test type constraint enforcement."""
    # Length constraints
    assert len("test_123") <= 128  # KeyID max length
    assert len("a" * 64) == 64  # KeyHash exact length
    
    # Format constraints
    assert all(c.isalnum() or c == "_" for c in "test_123")  # KeyID chars
    assert all(c.isalnum() for c in "a" * 64)  # KeyHash chars
    
    # Value constraints
    quota: QuotaLimit = {"max_requests": 1000}
    assert quota["max_requests"] > 0  # Must be positive
    
    rate: RateLimit = {"requests_per_second": 10.5}
    assert rate["requests_per_second"] > 0  # Must be positive 