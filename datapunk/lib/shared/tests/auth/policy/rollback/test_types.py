import pytest
from datetime import datetime, timedelta
from datapunk_shared.auth.policy.rollback.types import (
    RollbackStatus, RollbackRisk, RollbackContext, RollbackResult
)

def test_rollback_status_enum():
    """Test RollbackStatus enum values."""
    assert RollbackStatus.PENDING.value == "pending"
    assert RollbackStatus.IN_PROGRESS.value == "in_progress"
    assert RollbackStatus.COMPLETED.value == "completed"
    assert RollbackStatus.FAILED.value == "failed"
    assert RollbackStatus.CANCELLED.value == "cancelled"

def test_rollback_risk_enum():
    """Test RollbackRisk enum values."""
    assert RollbackRisk.LOW.value == "low"
    assert RollbackRisk.MEDIUM.value == "medium"
    assert RollbackRisk.HIGH.value == "high"
    assert RollbackRisk.CRITICAL.value == "critical"

def test_rollback_context_creation():
    """Test RollbackContext creation and properties."""
    now = datetime.utcnow()
    context = RollbackContext(
        rollback_id="rollback-001",
        policy_id="policy-001",
        initiator_id="user-001",
        timestamp=now,
        reason="Test rollback",
        affected_services=["service1", "service2"],
        metadata={"ticket": "TICKET-001"}
    )
    
    assert context.rollback_id == "rollback-001"
    assert context.policy_id == "policy-001"
    assert context.initiator_id == "user-001"
    assert context.timestamp == now
    assert context.reason == "Test rollback"
    assert context.affected_services == ["service1", "service2"]
    assert context.metadata == {"ticket": "TICKET-001"}

def test_rollback_context_optional_metadata():
    """Test RollbackContext creation without optional metadata."""
    context = RollbackContext(
        rollback_id="rollback-001",
        policy_id="policy-001",
        initiator_id="user-001",
        timestamp=datetime.utcnow(),
        reason="Test rollback",
        affected_services=["service1"]
    )
    
    assert context.metadata is None

def test_rollback_result_creation():
    """Test RollbackResult creation and properties."""
    now = datetime.utcnow()
    result = RollbackResult(
        success=True,
        status=RollbackStatus.COMPLETED,
        start_time=now,
        end_time=now + timedelta(minutes=5),
        affected_resources=["resource1", "resource2"],
        metrics={"duration_ms": 5000}
    )
    
    assert result.success is True
    assert result.status == RollbackStatus.COMPLETED
    assert result.start_time == now
    assert result.end_time == now + timedelta(minutes=5)
    assert result.error_message is None
    assert result.affected_resources == ["resource1", "resource2"]
    assert result.metrics == {"duration_ms": 5000}

def test_rollback_result_failed():
    """Test RollbackResult creation for failed rollback."""
    now = datetime.utcnow()
    result = RollbackResult(
        success=False,
        status=RollbackStatus.FAILED,
        start_time=now,
        end_time=now + timedelta(minutes=1),
        error_message="Rollback failed due to validation error",
        affected_resources=[],
        metrics={"error_code": 500}
    )
    
    assert result.success is False
    assert result.status == RollbackStatus.FAILED
    assert result.error_message == "Rollback failed due to validation error"
    assert result.affected_resources == []
    assert result.metrics == {"error_code": 500}

def test_rollback_result_in_progress():
    """Test RollbackResult creation for in-progress rollback."""
    now = datetime.utcnow()
    result = RollbackResult(
        success=False,  # Not yet successful
        status=RollbackStatus.IN_PROGRESS,
        start_time=now,
        end_time=None,  # Still running
        affected_resources=["resource1"],
        metrics={"progress_percent": 50}
    )
    
    assert result.success is False
    assert result.status == RollbackStatus.IN_PROGRESS
    assert result.start_time == now
    assert result.end_time is None
    assert result.error_message is None
    assert result.affected_resources == ["resource1"]
    assert result.metrics == {"progress_percent": 50}

def test_rollback_context_affected_services_immutability():
    """Test that RollbackContext affected_services can't be modified after creation."""
    services = ["service1", "service2"]
    context = RollbackContext(
        rollback_id="rollback-001",
        policy_id="policy-001",
        initiator_id="user-001",
        timestamp=datetime.utcnow(),
        reason="Test rollback",
        affected_services=services
    )
    
    # Modify original list
    services.append("service3")
    
    # Verify context services weren't modified
    assert "service3" not in context.affected_services

def test_rollback_result_affected_resources_immutability():
    """Test that RollbackResult affected_resources can't be modified after creation."""
    resources = ["resource1", "resource2"]
    result = RollbackResult(
        success=True,
        status=RollbackStatus.COMPLETED,
        start_time=datetime.utcnow(),
        affected_resources=resources
    )
    
    # Modify original list
    resources.append("resource3")
    
    # Verify result resources weren't modified
    assert "resource3" not in result.affected_resources

def test_rollback_result_metrics_immutability():
    """Test that RollbackResult metrics can't be modified after creation."""
    metrics = {"duration_ms": 5000}
    result = RollbackResult(
        success=True,
        status=RollbackStatus.COMPLETED,
        start_time=datetime.utcnow(),
        affected_resources=[],
        metrics=metrics
    )
    
    # Modify original dict
    metrics["new_metric"] = "value"
    
    # Verify result metrics weren't modified
    assert "new_metric" not in result.metrics

def test_rollback_context_metadata_immutability():
    """Test that RollbackContext metadata can't be modified after creation."""
    metadata = {"ticket": "TICKET-001"}
    context = RollbackContext(
        rollback_id="rollback-001",
        policy_id="policy-001",
        initiator_id="user-001",
        timestamp=datetime.utcnow(),
        reason="Test rollback",
        affected_services=[],
        metadata=metadata
    )
    
    # Modify original dict
    metadata["new_field"] = "value"
    
    # Verify context metadata wasn't modified
    assert "new_field" not in context.metadata 