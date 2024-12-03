"""Tests for circuit breaker request prioritization"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from datapunk_shared.mesh.circuit_breaker.request_priority import (
    RequestPriority,
    PriorityConfig,
    PriorityManager
)
from datapunk_shared.mesh.circuit_breaker.circuit_breaker_strategies import (
    CircuitState
)

@pytest.fixture
def mock_metrics():
    metrics = AsyncMock()
    metrics.increment = AsyncMock()
    metrics.gauge = AsyncMock()
    return metrics

@pytest.fixture
def priority_config():
    return PriorityConfig(
        min_priority=RequestPriority.LOW.value,
        reserved_slots={
            RequestPriority.CRITICAL: 2,
            RequestPriority.HIGH: 4,
            RequestPriority.NORMAL: 8
        },
        timeout_ms={
            RequestPriority.CRITICAL: 1000,
            RequestPriority.HIGH: 500,
            RequestPriority.NORMAL: 200
        }
    )

@pytest.fixture
def priority_manager(priority_config, mock_metrics):
    return PriorityManager(priority_config, mock_metrics)

class TestRequestPriority:
    def test_priority_ordering(self):
        """Test priority level relationships"""
        assert RequestPriority.CRITICAL.value > RequestPriority.HIGH.value
        assert RequestPriority.HIGH.value > RequestPriority.NORMAL.value
        assert RequestPriority.NORMAL.value > RequestPriority.LOW.value
        assert RequestPriority.LOW.value > RequestPriority.BULK.value

class TestPriorityConfig:
    def test_default_config(self):
        """Test default configuration values"""
        config = PriorityConfig()
        
        assert config.min_priority == 0
        assert RequestPriority.CRITICAL in config.reserved_slots
        assert RequestPriority.CRITICAL in config.timeout_ms
        
    def test_custom_config(self):
        """Test custom configuration values"""
        config = PriorityConfig(
            min_priority=50,
            reserved_slots={RequestPriority.CRITICAL: 1},
            timeout_ms={RequestPriority.CRITICAL: 2000}
        )
        
        assert config.min_priority == 50
        assert config.reserved_slots[RequestPriority.CRITICAL] == 1
        assert config.timeout_ms[RequestPriority.CRITICAL] == 2000

class TestPriorityManager:
    async def test_critical_request_always_allowed(self, priority_manager):
        """Test that critical requests are always allowed"""
        allowed = await priority_manager.can_execute(
            RequestPriority.CRITICAL,
            CircuitState.OPEN
        )
        assert allowed
        
    async def test_below_min_priority_blocked(self, priority_manager):
        """Test that requests below minimum priority are blocked"""
        priority_manager.config.min_priority = RequestPriority.NORMAL.value
        
        allowed = await priority_manager.can_execute(
            RequestPriority.LOW,
            CircuitState.CLOSED
        )
        assert not allowed
        
    async def test_open_circuit_blocks_noncritical(self, priority_manager):
        """Test that open circuit blocks non-critical requests"""
        allowed = await priority_manager.can_execute(
            RequestPriority.HIGH,
            CircuitState.OPEN
        )
        assert not allowed
        
    async def test_half_open_allows_high_priority(self, priority_manager):
        """Test that half-open circuit allows high priority requests"""
        allowed = await priority_manager.can_execute(
            RequestPriority.HIGH,
            CircuitState.HALF_OPEN
        )
        assert allowed
        
        allowed = await priority_manager.can_execute(
            RequestPriority.NORMAL,
            CircuitState.HALF_OPEN
        )
        assert not allowed
        
    async def test_reserved_slots_enforcement(self, priority_manager):
        """Test that reserved slots are enforced"""
        # Fill up reserved slots
        priority = RequestPriority.HIGH
        slots = priority_manager.config.reserved_slots[priority]
        
        for _ in range(slots):
            priority_manager.active_requests[priority] += 1
            
        allowed = await priority_manager.can_execute(
            priority,
            CircuitState.CLOSED
        )
        assert not allowed
        
    async def test_request_queuing(self, priority_manager):
        """Test request queuing behavior"""
        # Start request
        started = await priority_manager.start_request(
            RequestPriority.NORMAL
        )
        assert started
        assert priority_manager.get_active_requests(RequestPriority.NORMAL) == 1
        
        # Complete request
        await priority_manager.finish_request(RequestPriority.NORMAL)
        assert priority_manager.get_active_requests(RequestPriority.NORMAL) == 0
        
    async def test_request_timeout(self, priority_manager):
        """Test request timeout behavior"""
        # Set very short timeout
        priority_manager.config.timeout_ms[RequestPriority.LOW] = 1
        
        # Start request that will timeout
        started = await priority_manager.start_request(
            RequestPriority.LOW
        )
        assert not started
        
    async def test_dynamic_priority_adjustment(self, priority_manager):
        """Test dynamic priority threshold adjustment"""
        new_min = RequestPriority.HIGH.value
        await priority_manager.adjust_min_priority(new_min)
        
        assert priority_manager.config.min_priority == new_min
        
    async def test_dynamic_slot_adjustment(self, priority_manager):
        """Test dynamic slot reservation adjustment"""
        new_slots = 10
        await priority_manager.adjust_reserved_slots(
            RequestPriority.HIGH,
            new_slots
        )
        
        assert priority_manager.config.reserved_slots[RequestPriority.HIGH] == new_slots
        
    async def test_metrics_recording(self, priority_manager, mock_metrics):
        """Test that metrics are recorded"""
        await priority_manager.can_execute(
            RequestPriority.NORMAL,
            CircuitState.CLOSED
        )
        
        mock_metrics.increment.assert_awaited_once_with(
            "circuit_breaker_priority_check",
            {"priority": "NORMAL"}
        )
        
    async def test_queue_processing(self, priority_manager):
        """Test queue processing on request completion"""
        priority = RequestPriority.NORMAL
        
        # Fill up slots
        slots = priority_manager.config.reserved_slots[priority]
        for _ in range(slots):
            await priority_manager.start_request(priority)
            
        # Queue additional request
        import asyncio
        event = asyncio.Event()
        priority_manager.queued_requests[priority].append(event)
        
        # Complete a request
        await priority_manager.finish_request(priority)
        
        # Verify queued request was processed
        assert event.is_set()
        
    async def test_request_tracking(self, priority_manager):
        """Test request tracking counters"""
        priority = RequestPriority.HIGH
        
        # Start requests
        await priority_manager.start_request(priority)
        await priority_manager.start_request(priority)
        
        assert priority_manager.get_active_requests(priority) == 2
        
        # Complete requests
        await priority_manager.finish_request(priority)
        
        assert priority_manager.get_active_requests(priority) == 1 