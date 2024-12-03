"""Tests for partial recovery management"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from datapunk_shared.mesh.circuit_breaker.partial_recovery import (
    FeatureState,
    FeatureHealth,
    FeatureConfig,
    FeatureStatus,
    PartialRecoveryManager
)

@pytest.fixture
def mock_metrics():
    metrics = AsyncMock()
    metrics.increment = AsyncMock()
    return metrics

@pytest.fixture
def feature_configs():
    return {
        "auth": FeatureConfig(
            name="auth",
            priority=1,
            dependencies=set(),
            required=True
        ),
        "api": FeatureConfig(
            name="api",
            priority=2,
            dependencies={"auth"}
        ),
        "websocket": FeatureConfig(
            name="websocket",
            priority=2,
            dependencies={"auth"}
        ),
        "notifications": FeatureConfig(
            name="notifications",
            priority=3,
            dependencies={"api", "websocket"}
        )
    }

@pytest.fixture
def recovery_manager(mock_metrics, feature_configs):
    return PartialRecoveryManager(
        features=feature_configs,
        metrics_client=mock_metrics
    )

class TestFeatureConfig:
    def test_feature_config_defaults(self):
        config = FeatureConfig(
            name="test",
            priority=1,
            dependencies=set()
        )
        
        assert config.min_health_threshold == 0.8
        assert config.test_duration_seconds == 30
        assert not config.required
        
    def test_feature_config_custom(self):
        config = FeatureConfig(
            name="test",
            priority=1,
            dependencies={"auth"},
            min_health_threshold=0.9,
            test_duration_seconds=60,
            required=True
        )
        
        assert config.min_health_threshold == 0.9
        assert config.test_duration_seconds == 60
        assert config.required

class TestFeatureStatus:
    def test_initial_status(self):
        config = FeatureConfig("test", 1, set())
        status = FeatureStatus(config)
        
        assert status.state == FeatureState.DISABLED
        assert status.health == FeatureHealth.UNKNOWN
        assert status.success_count == 0
        assert status.error_count == 0
        
    def test_success_rate_calculation(self):
        config = FeatureConfig("test", 1, set())
        status = FeatureStatus(config)
        
        # No requests
        assert status.success_rate == 1.0
        
        # All successful
        status.success_count = 5
        assert status.success_rate == 1.0
        
        # Mixed results
        status.error_count = 5
        assert status.success_rate == 0.5
        
    def test_reset_counters(self):
        config = FeatureConfig("test", 1, set())
        status = FeatureStatus(config)
        
        status.success_count = 5
        status.error_count = 3
        status.reset_counters()
        
        assert status.success_count == 0
        assert status.error_count == 0
        
    def test_health_update(self):
        config = FeatureConfig("test", 1, set())
        status = FeatureStatus(config)
        
        # Healthy
        status.success_count = 9
        status.error_count = 1
        status.update_health()
        assert status.health == FeatureHealth.HEALTHY
        
        # Degraded
        status.success_count = 7
        status.error_count = 3
        status.update_health()
        assert status.health == FeatureHealth.DEGRADED
        
        # Unhealthy
        status.success_count = 5
        status.error_count = 5
        status.update_health()
        assert status.health == FeatureHealth.UNHEALTHY

class TestPartialRecoveryManager:
    def test_initialization(self, recovery_manager, feature_configs):
        assert len(recovery_manager.status) == len(feature_configs)
        
        # Verify dependency graph
        assert "api" in recovery_manager.dependents["auth"]
        assert "websocket" in recovery_manager.dependents["auth"]
        assert "notifications" in recovery_manager.dependents["api"]
        
    @pytest.mark.asyncio
    async def test_start_recovery(self, recovery_manager):
        await recovery_manager.start_recovery()
        
        assert recovery_manager.recovery_start_time is not None
        assert recovery_manager.recovery_phase == 1
        recovery_manager.metrics.increment.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_feature_testing(self, recovery_manager):
        # Test auth feature (no dependencies)
        await recovery_manager.test_feature("auth")
        auth_status = recovery_manager.status["auth"]
        assert auth_status.state == FeatureState.TESTING
        
        # Test API feature (depends on auth)
        await recovery_manager.test_feature("api")
        api_status = recovery_manager.status["api"]
        assert api_status.state == FeatureState.DISABLED  # Auth not enabled
        
    @pytest.mark.asyncio
    async def test_feature_result_recording(self, recovery_manager):
        await recovery_manager.test_feature("auth")
        
        # Record successful results
        for _ in range(8):
            await recovery_manager.record_result("auth", True)
            
        # Record some failures
        for _ in range(2):
            await recovery_manager.record_result("auth", False)
            
        status = recovery_manager.status["auth"]
        assert status.success_count == 8
        assert status.error_count == 2
        assert status.success_rate == 0.8
        
    @pytest.mark.asyncio
    async def test_feature_enablement(self, recovery_manager):
        await recovery_manager.test_feature("auth")
        
        # Make feature healthy
        for _ in range(10):
            await recovery_manager.record_result("auth", True)
            
        # Fast forward test duration
        status = recovery_manager.status["auth"]
        status.last_test_start = (
            datetime.utcnow() - 
            timedelta(seconds=status.config.test_duration_seconds + 1)
        )
        
        # Record one more result to trigger test completion
        await recovery_manager.record_result("auth", True)
        
        assert status.state == FeatureState.ENABLED
        
    @pytest.mark.asyncio
    async def test_dependency_chain(self, recovery_manager):
        # Enable auth
        await recovery_manager.test_feature("auth")
        for _ in range(10):
            await recovery_manager.record_result("auth", True)
            
        # Fast forward and complete auth test
        auth_status = recovery_manager.status["auth"]
        auth_status.last_test_start = (
            datetime.utcnow() - 
            timedelta(seconds=auth_status.config.test_duration_seconds + 1)
        )
        await recovery_manager.record_result("auth", True)
        
        # Now API should be testable
        await recovery_manager.test_feature("api")
        api_status = recovery_manager.status["api"]
        assert api_status.state == FeatureState.TESTING
        
    @pytest.mark.asyncio
    async def test_required_feature_rollback(self, recovery_manager):
        await recovery_manager.test_feature("auth")
        
        # Make auth unhealthy
        for _ in range(10):
            await recovery_manager.record_result("auth", False)
            
        # Fast forward and complete test
        auth_status = recovery_manager.status["auth"]
        auth_status.last_test_start = (
            datetime.utcnow() - 
            timedelta(seconds=auth_status.config.test_duration_seconds + 1)
        )
        await recovery_manager.record_result("auth", False)
        
        # All features should be disabled
        for status in recovery_manager.status.values():
            assert status.state == FeatureState.DISABLED
            
    def test_feature_availability_check(self, recovery_manager):
        # Initially all disabled
        assert not recovery_manager.is_feature_available("auth")
        assert not recovery_manager.is_feature_available("api")
        
        # Enable auth
        recovery_manager.status["auth"].state = FeatureState.ENABLED
        assert recovery_manager.is_feature_available("auth")
        
    def test_feature_metrics(self, recovery_manager):
        # Add some test data
        auth_status = recovery_manager.status["auth"]
        auth_status.success_count = 8
        auth_status.error_count = 2
        auth_status.state = FeatureState.TESTING
        auth_status.update_health()
        
        metrics = recovery_manager.get_feature_metrics()
        
        auth_metrics = metrics["feature_auth"]
        assert auth_metrics["state"] == "testing"
        assert auth_metrics["success_rate"] == 0.8
        assert auth_metrics["success_count"] == 8
        assert auth_metrics["error_count"] == 2 