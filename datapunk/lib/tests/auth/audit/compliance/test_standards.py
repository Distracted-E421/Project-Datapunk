"""
Compliance Standards Tests
----------------------

Tests the compliance standards implementation including:
- Standard definitions and validation
- Rule processing and evaluation
- Metric calculations
- Standard versioning
- Requirement levels
- Validation rules

Run with: pytest -v test_standards.py
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
import json

from datapunk_shared.auth.audit.compliance.standards import (
    ComplianceStandard,
    StandardType,
    ValidationRule,
    RequirementLevel,
    ComplianceMetric,
    ComplianceRule
)

# Test Fixtures

@pytest.fixture
def validation_rule():
    """Create validation rule for testing."""
    return ValidationRule(
        field="access_type",
        condition="in",
        values=["read", "write", "admin"],
        description="Valid access types"
    )

@pytest.fixture
def compliance_rule():
    """Create compliance rule for testing."""
    return ComplianceRule(
        id="ACC-1",
        name="Access Control",
        description="Access control requirements",
        level=RequirementLevel.REQUIRED,
        validation_rules=[
            ValidationRule(
                field="access_type",
                condition="in",
                values=["read", "write", "admin"]
            ),
            ValidationRule(
                field="user_id",
                condition="exists",
                values=None
            )
        ]
    )

@pytest.fixture
def compliance_standard():
    """Create compliance standard for testing."""
    return ComplianceStandard(
        id="SOC2",
        name="SOC 2",
        version="2022",
        description="SOC 2 compliance standard",
        requirements=[
            ComplianceRule(
                id="ACC-1",
                name="Access Control",
                level=RequirementLevel.REQUIRED,
                validation_rules=[
                    ValidationRule(
                        field="access_type",
                        condition="in",
                        values=["read", "write", "admin"]
                    )
                ]
            ),
            ComplianceRule(
                id="LOG-1",
                name="Audit Logging",
                level=RequirementLevel.REQUIRED,
                validation_rules=[
                    ValidationRule(
                        field="event_type",
                        condition="exists",
                        values=None
                    )
                ]
            )
        ]
    )

# Standard Definition Tests

def test_standard_creation(compliance_standard):
    """Test compliance standard creation."""
    assert compliance_standard.id == "SOC2"
    assert compliance_standard.version == "2022"
    assert len(compliance_standard.requirements) == 2
    
    # Verify requirements structure
    assert all(isinstance(r, ComplianceRule) for r in compliance_standard.requirements)
    assert all(r.level == RequirementLevel.REQUIRED for r in compliance_standard.requirements)

def test_standard_validation():
    """Test standard validation rules."""
    # Invalid standard ID
    with pytest.raises(ValueError) as exc:
        ComplianceStandard(
            id="",  # Empty ID
            name="Test",
            version="1.0",
            requirements=[]
        )
    assert "invalid standard id" in str(exc.value).lower()
    
    # Invalid version format
    with pytest.raises(ValueError) as exc:
        ComplianceStandard(
            id="TEST",
            name="Test",
            version="invalid",  # Invalid version
            requirements=[]
        )
    assert "invalid version format" in str(exc.value).lower()

def test_standard_serialization(compliance_standard):
    """Test standard serialization."""
    # Convert to dict
    data = compliance_standard.to_dict()
    assert isinstance(data, dict)
    assert data["id"] == "SOC2"
    assert "requirements" in data
    
    # Convert to JSON
    json_data = json.dumps(data)
    assert isinstance(json_data, str)
    
    # Deserialize
    loaded = ComplianceStandard.from_dict(json.loads(json_data))
    assert isinstance(loaded, ComplianceStandard)
    assert loaded.id == compliance_standard.id
    assert len(loaded.requirements) == len(compliance_standard.requirements)

# Rule Processing Tests

def test_rule_validation(compliance_rule):
    """Test compliance rule validation."""
    # Valid event
    event = {
        "access_type": "read",
        "user_id": "test_user"
    }
    assert compliance_rule.validate(event) is True
    
    # Invalid access type
    event = {
        "access_type": "invalid",
        "user_id": "test_user"
    }
    assert compliance_rule.validate(event) is False
    
    # Missing required field
    event = {
        "access_type": "read"
        # Missing user_id
    }
    assert compliance_rule.validate(event) is False

def test_rule_requirement_levels():
    """Test different requirement levels."""
    # Required rule
    required_rule = ComplianceRule(
        id="REQ-1",
        name="Required Rule",
        level=RequirementLevel.REQUIRED,
        validation_rules=[
            ValidationRule(
                field="test",
                condition="exists",
                values=None
            )
        ]
    )
    assert required_rule.validate({"other": "value"}) is False
    
    # Recommended rule
    recommended_rule = ComplianceRule(
        id="REC-1",
        name="Recommended Rule",
        level=RequirementLevel.RECOMMENDED,
        validation_rules=[
            ValidationRule(
                field="test",
                condition="exists",
                values=None
            )
        ]
    )
    # Should not fail validation if recommended rule fails
    assert recommended_rule.validate({"other": "value"}) is True

def test_validation_conditions(validation_rule):
    """Test different validation conditions."""
    # Test 'in' condition
    assert validation_rule.validate({"access_type": "read"}) is True
    assert validation_rule.validate({"access_type": "invalid"}) is False
    
    # Test 'exists' condition
    exists_rule = ValidationRule(
        field="test",
        condition="exists",
        values=None
    )
    assert exists_rule.validate({"test": "value"}) is True
    assert exists_rule.validate({"other": "value"}) is False
    
    # Test 'pattern' condition
    pattern_rule = ValidationRule(
        field="email",
        condition="pattern",
        values=["^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"]
    )
    assert pattern_rule.validate({"email": "test@example.com"}) is True
    assert pattern_rule.validate({"email": "invalid"}) is False

# Metric Calculation Tests

def test_compliance_metrics():
    """Test compliance metric calculations."""
    metric = ComplianceMetric(
        total_checks=100,
        passed_checks=75,
        failed_checks=25,
        start_time=datetime.utcnow() - timedelta(days=1),
        end_time=datetime.utcnow()
    )
    
    assert metric.compliance_rate == 0.75
    assert metric.failure_rate == 0.25
    assert metric.duration.days == 1

def test_metric_aggregation():
    """Test metric aggregation."""
    metrics = [
        ComplianceMetric(total_checks=100, passed_checks=80, failed_checks=20),
        ComplianceMetric(total_checks=100, passed_checks=90, failed_checks=10),
        ComplianceMetric(total_checks=100, passed_checks=70, failed_checks=30)
    ]
    
    aggregated = ComplianceMetric.aggregate(metrics)
    assert aggregated.total_checks == 300
    assert aggregated.passed_checks == 240
    assert aggregated.failed_checks == 60
    assert aggregated.compliance_rate == 0.8

# Version Management Tests

def test_version_compatibility():
    """Test standard version compatibility."""
    standard_v1 = ComplianceStandard(
        id="TEST",
        name="Test",
        version="1.0",
        requirements=[]
    )
    
    standard_v2 = ComplianceStandard(
        id="TEST",
        name="Test",
        version="2.0",
        requirements=[]
    )
    
    # Version comparison
    assert standard_v2.version > standard_v1.version
    
    # Version validation
    with pytest.raises(ValueError):
        ComplianceStandard(
            id="TEST",
            name="Test",
            version="invalid.version",
            requirements=[]
        )

def test_version_migration():
    """Test standard version migration."""
    old_standard = ComplianceStandard(
        id="TEST",
        name="Test",
        version="1.0",
        requirements=[
            ComplianceRule(
                id="OLD-1",
                name="Old Rule",
                level=RequirementLevel.REQUIRED,
                validation_rules=[]
            )
        ]
    )
    
    new_standard = ComplianceStandard(
        id="TEST",
        name="Test",
        version="2.0",
        requirements=[
            ComplianceRule(
                id="NEW-1",
                name="New Rule",
                level=RequirementLevel.REQUIRED,
                validation_rules=[]
            )
        ]
    )
    
    # Verify version differences
    assert old_standard.version != new_standard.version
    assert old_standard.requirements[0].id != new_standard.requirements[0].id

# Error Handling Tests

def test_invalid_rule_definition():
    """Test handling of invalid rule definitions."""
    # Invalid rule ID
    with pytest.raises(ValueError):
        ComplianceRule(
            id="",  # Empty ID
            name="Test",
            level=RequirementLevel.REQUIRED,
            validation_rules=[]
        )
    
    # Invalid validation rule
    with pytest.raises(ValueError):
        ValidationRule(
            field="test",
            condition="invalid_condition",  # Invalid condition
            values=None
        )

def test_validation_error_handling(compliance_rule):
    """Test validation error handling."""
    # Invalid field type
    event = {
        "access_type": 123,  # Should be string
        "user_id": "test"
    }
    assert compliance_rule.validate(event) is False
    
    # Invalid field format
    event = {
        "access_type": "read",
        "user_id": ""  # Empty string
    }
    assert compliance_rule.validate(event) is False 