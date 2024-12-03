"""
Circuit Breaker Request Prioritization

Implements priority-based request handling for circuit breaker system.
Allows critical requests to proceed even during partial outages while
blocking less important traffic.

Key features:
- Request priority levels
- Dynamic priority adjustment
- Resource reservation
- Priority inheritance
- Priority-based queuing
"""

from typing import Optional, Dict, Any, List
from enum import Enum
import asyncio
import structlog
from datetime import datetime, timedelta
from .circuit_breaker_strategies import CircuitState

logger = structlog.get_logger()

class RequestPriority(Enum):
    """Priority levels for circuit breaker requests"""
    CRITICAL = 100  # System critical operations
    HIGH = 75      # Important business operations
    NORMAL = 50    # Standard requests
    LOW = 25       # Background tasks
    BULK = 0       # Batch operations

class PriorityConfig:
    """Configuration for priority-based handling"""
    def __init__(self,
                 min_priority: int = 0,
                 reserved_slots: Dict[RequestPriority, int] = None,
                 timeout_ms: Dict[RequestPriority, int] = None):
        self.min_priority = min_priority
        self.reserved_slots = reserved_slots or {
            RequestPriority.CRITICAL: 5,
            RequestPriority.HIGH: 10,
            RequestPriority.NORMAL: 20
        }
        self.timeout_ms = timeout_ms or {
            RequestPriority.CRITICAL: 5000,
            RequestPriority.HIGH: 2000,
            RequestPriority.NORMAL: 1000,
            RequestPriority.LOW: 500,
            RequestPriority.BULK: 100
        }

class PriorityManager:
    """
    Manages priority-based request handling.
    
    Features:
    - Priority-based admission control
    - Resource reservation by priority
    - Dynamic priority adjustment
    - Request queuing
    """
    
    def __init__(self,
                 config: PriorityConfig,
                 metrics_client=None):
        self.config = config
        self.metrics = metrics_client
        self.active_requests: Dict[RequestPriority, int] = {
            p: 0 for p in RequestPriority
        }
        self.queued_requests: Dict[RequestPriority, List[asyncio.Event]] = {
            p: [] for p in RequestPriority
        }
        self.logger = logger.bind(component="priority_manager")
        
    async def can_execute(self,
                         priority: RequestPriority,
                         circuit_state: CircuitState) -> bool:
        """
        Check if request can proceed based on priority.
        
        Implements:
        1. Priority threshold checks
        2. Resource reservation verification
        3. Circuit state consideration
        4. Queue management
        """
        # Record attempt metric
        if self.metrics:
            await self.metrics.increment(
                "circuit_breaker_priority_check",
                {"priority": priority.name}
            )
            
        # Check minimum priority threshold
        if priority.value < self.config.min_priority:
            self.logger.debug("request_below_min_priority",
                            priority=priority.name)
            return False
            
        # Always allow critical requests
        if priority == RequestPriority.CRITICAL:
            return True
            
        # Check circuit state
        if circuit_state == CircuitState.OPEN:
            # Only allow critical requests when open
            return False
            
        if circuit_state == CircuitState.HALF_OPEN:
            # Higher bar for half-open state
            return priority.value >= RequestPriority.HIGH.value
            
        # Check resource reservation
        reserved = self.config.reserved_slots.get(priority, 0)
        active = self.active_requests[priority]
        
        if active >= reserved:
            self.logger.debug("no_reserved_slots",
                            priority=priority.name,
                            active=active,
                            reserved=reserved)
            return False
            
        return True
        
    async def start_request(self,
                          priority: RequestPriority,
                          timeout_ms: Optional[int] = None) -> bool:
        """
        Start tracking a new request.
        
        Returns:
            bool: True if request can start, False if rejected
        """
        if not await self.can_execute(priority, CircuitState.CLOSED):
            return False
            
        # Use priority-specific timeout
        timeout = timeout_ms or self.config.timeout_ms.get(
            priority,
            1000  # Default 1 second
        )
        
        # Try to queue request
        event = asyncio.Event()
        self.queued_requests[priority].append(event)
        
        try:
            # Wait for execution slot
            await asyncio.wait_for(
                event.wait(),
                timeout=timeout/1000.0
            )
            
            # Track active request
            self.active_requests[priority] += 1
            
            if self.metrics:
                await self.metrics.increment(
                    "circuit_breaker_request_started",
                    {"priority": priority.name}
                )
            
            return True
            
        except asyncio.TimeoutError:
            # Remove from queue on timeout
            self.queued_requests[priority].remove(event)
            
            if self.metrics:
                await self.metrics.increment(
                    "circuit_breaker_request_timeout",
                    {"priority": priority.name}
                )
            
            return False
            
    async def finish_request(self, priority: RequestPriority):
        """Mark request as complete and process queue"""
        self.active_requests[priority] -= 1
        
        if self.metrics:
            await self.metrics.increment(
                "circuit_breaker_request_completed",
                {"priority": priority.name}
            )
        
        # Process queued requests
        while self.queued_requests[priority]:
            if await self.can_execute(priority, CircuitState.CLOSED):
                # Release next queued request
                event = self.queued_requests[priority].pop(0)
                event.set()
            else:
                break
                
    def get_active_requests(self, priority: RequestPriority) -> int:
        """Get number of active requests for priority level"""
        return self.active_requests[priority]
        
    def get_queued_requests(self, priority: RequestPriority) -> int:
        """Get number of queued requests for priority level"""
        return len(self.queued_requests[priority])
        
    async def adjust_min_priority(self, new_min: int):
        """
        Dynamically adjust minimum priority threshold.
        
        Used to shed load during high traffic periods.
        """
        old_min = self.config.min_priority
        self.config.min_priority = new_min
        
        if self.metrics:
            await self.metrics.gauge(
                "circuit_breaker_min_priority",
                new_min
            )
            
        self.logger.info("min_priority_adjusted",
                        old=old_min,
                        new=new_min)
        
    async def adjust_reserved_slots(self,
                                  priority: RequestPriority,
                                  slots: int):
        """
        Dynamically adjust reserved slots for priority level.
        
        Used to rebalance resources based on traffic patterns.
        """
        old_slots = self.config.reserved_slots.get(priority, 0)
        self.config.reserved_slots[priority] = slots
        
        if self.metrics:
            await self.metrics.gauge(
                "circuit_breaker_reserved_slots",
                slots,
                {"priority": priority.name}
            )
            
        self.logger.info("reserved_slots_adjusted",
                        priority=priority.name,
                        old=old_slots,
                        new=slots) 