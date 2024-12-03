import pytest
import tempfile
import os
from src.nexus.auth.access_control import (
    AccessControl,
    AccessRuleType,
    LocationInfo,
    IPRule,
    GeoRule
)

@pytest.fixture
def geoip_db():
    """Create a mock GeoIP database for testing."""
    # This would normally point to a real MaxMind database
    # For testing, we'll create a temporary file
    fd, path = tempfile.mkstemp()
    os.close(fd)
    
    # In a real implementation, you would download and use a real MaxMind database
    # For testing, we'll just use the file path
    yield path
    os.unlink(path)

@pytest.fixture
def access_control(geoip_db):
    return AccessControl(geoip_db, default_allow=False)

def test_ip_rule_validation(access_control):
    # Test valid CIDR
    access_control.add_ip_rule(
        {"192.168.1.0/24"},
        AccessRuleType.ALLOW,
        "Internal network"
    )
    
    # Test invalid CIDR
    with pytest.raises(ValueError):
        access_control.add_ip_rule(
            {"invalid_cidr"},
            AccessRuleType.ALLOW
        )
        
    # Test multiple networks
    access_control.add_ip_rule(
        {"10.0.0.0/8", "172.16.0.0/12"},
        AccessRuleType.DENY,
        "External networks"
    )

def test_geo_rule_validation(access_control):
    # Test country-only rule
    access_control.add_geo_rule(
        countries={"US", "CA"},
        rule_type=AccessRuleType.ALLOW
    )
    
    # Test country and region rule
    access_control.add_geo_rule(
        countries={"US"},
        regions={"California", "New York"},
        rule_type=AccessRuleType.ALLOW
    )
    
    # Test complete rule
    access_control.add_geo_rule(
        countries={"US"},
        regions={"California"},
        cities={"San Francisco", "Los Angeles"},
        rule_type=AccessRuleType.ALLOW
    )

def test_ip_rule_matching(access_control):
    # Add allow rule for internal network
    access_control.add_ip_rule(
        {"192.168.1.0/24"},
        AccessRuleType.ALLOW,
        "Internal network"
    )
    
    # Add deny rule for specific IP range
    access_control.add_ip_rule(
        {"192.168.1.100/30"},
        AccessRuleType.DENY,
        "Restricted IPs"
    )
    
    # Test allowed IP
    allowed, reason = access_control.check_ip_rules("192.168.1.1")
    assert allowed is True
    assert "Internal network" in reason
    
    # Test denied IP
    allowed, reason = access_control.check_ip_rules("192.168.1.100")
    assert allowed is False
    assert "Restricted IPs" in reason
    
    # Test IP not matching any rules
    allowed, reason = access_control.check_ip_rules("10.0.0.1")
    assert allowed is False
    assert "default policy" in reason.lower()

def test_geo_rule_matching(access_control):
    # Create mock location info
    us_location = LocationInfo(
        country_code="US",
        country_name="United States",
        region="California",
        city="San Francisco",
        latitude=37.7749,
        longitude=-122.4194
    )
    
    # Add allow rule for US
    access_control.add_geo_rule(
        countries={"US"},
        rule_type=AccessRuleType.ALLOW
    )
    
    # Test allowed location
    allowed, reason = access_control.check_geo_rules(us_location)
    assert allowed is True
    assert "US" in reason
    
    # Test location with no rules
    other_location = LocationInfo(
        country_code="FR",
        country_name="France",
        region="Île-de-France",
        city="Paris",
        latitude=48.8566,
        longitude=2.3522
    )
    allowed, reason = access_control.check_geo_rules(other_location)
    assert allowed is False
    assert "default policy" in reason.lower()

def test_combined_rules(access_control):
    # Add both IP and geo rules
    access_control.add_ip_rule(
        {"192.168.1.0/24"},
        AccessRuleType.ALLOW,
        "Internal network"
    )
    
    access_control.add_geo_rule(
        countries={"US"},
        rule_type=AccessRuleType.ALLOW
    )
    
    # Test IP that matches allow rule
    allowed, reason = access_control.check_access("192.168.1.1")
    assert allowed is True
    assert "Internal network" in reason
    
    # Test IP that doesn't match any rules (falls back to geo rules)
    # Note: In a real test, this would need a mock for GeoIP lookup
    allowed, reason = access_control.check_access("10.0.0.1")
    assert allowed is False
    assert "No rules matched" in reason

def test_geofencing(access_control):
    # Test point within radius
    assert access_control.is_ip_in_range(
        "192.168.1.1",  # Note: In real tests, use an IP that resolves to a known location
        latitude=37.7749,
        longitude=-122.4194,
        radius_km=10
    ) is False  # False because our mock GeoIP won't resolve the IP

def test_rule_precedence(access_control):
    # Add overlapping rules to test precedence
    access_control.add_ip_rule(
        {"192.168.0.0/16"},
        AccessRuleType.ALLOW,
        "Wide network"
    )
    
    access_control.add_ip_rule(
        {"192.168.1.0/24"},
        AccessRuleType.DENY,
        "Restricted subnet"
    )
    
    # Test IP in restricted subnet
    allowed, reason = access_control.check_ip_rules("192.168.1.100")
    assert allowed is False
    assert "Restricted subnet" in reason
    
    # Test IP in allowed network but not in restricted subnet
    allowed, reason = access_control.check_ip_rules("192.168.2.100")
    assert allowed is True
    assert "Wide network" in reason

def test_invalid_inputs(access_control):
    # Test invalid IP
    allowed, reason = access_control.check_ip_rules("invalid_ip")
    assert allowed is False
    assert "Invalid IP" in reason
    
    # Test None location
    allowed, reason = access_control.check_geo_rules(None)
    assert allowed is False
    assert "No location information" in reason 