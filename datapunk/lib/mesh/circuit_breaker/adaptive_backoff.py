"""
Adaptive Backoff System for Circuit Breaker

Provides intelligent backoff strategies that adapt to system conditions
and failure patterns. Supports multiple strategies with dynamic selection
based on effectiveness and resource conditions.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import random
import structlog
from enum import Enum
import math

logger = structlog.get_logger()

class BackoffStrategy(Enum):
    """Available backoff strategies"""
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"
    DECORRELATED_JITTER = "decorrelated_jitter"
    RESOURCE_SENSITIVE = "resource_sensitive"
    PATTERN_BASED = "pattern_based"
    ADAPTIVE = "adaptive"

@dataclass
class BackoffConfig:
    """Configuration for backoff behavior"""
    initial_delay: float = 1.0  # Initial delay in seconds
    max_delay: float = 60.0     # Maximum delay in seconds
    multiplier: float = 2.0     # Multiplier for exponential backoff
    jitter: float = 0.1         # Jitter factor (0-1)
    pattern_window: int = 60    # Window for pattern analysis (seconds)
    resource_threshold: float = 0.8  # Resource utilization threshold

class BackoffState:
    """Tracks backoff state and history"""
    def __init__(self):
        self.attempt: int = 0
        self.last_delay: float = 0
        self.last_attempt: Optional[datetime] = None
        self.success_count: int = 0
        self.failure_count: int = 0
        self.delays: List[float] = []
        self.outcomes: List[bool] = []
        self.resource_states: List[float] = []

class AdaptiveBackoff:
    """
    Adaptive backoff system that dynamically selects and adjusts
    backoff strategies based on system conditions and failure patterns.
    
    Features:
    - Multiple backoff strategies
    - Dynamic strategy selection
    - Pattern-based adaptation
    - Resource awareness
    - Circuit state integration
    """
    
    def __init__(self, config: Optional[BackoffConfig] = None):
        """Initialize adaptive backoff system"""
        self.config = config or BackoffConfig()
        self.logger = logger.bind(component="adaptive_backoff")
        self.states: Dict[str, BackoffState] = {}
        self.strategy_effectiveness: Dict[BackoffStrategy, float] = {
            strategy: 1.0 for strategy in BackoffStrategy
        }
        self.pattern_history: List[Dict[str, Any]] = []
        self.current_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
        
    def _get_state(self, key: str) -> BackoffState:
        """Get or create backoff state for key"""
        if key not in self.states:
            self.states[key] = BackoffState()
        return self.states[key]
        
    async def get_delay(self, key: str, resource_usage: Optional[float] = None) -> float:
        """
        Calculate next backoff delay using the most effective strategy
        
        Args:
            key: Identifier for the backoff sequence
            resource_usage: Current resource utilization (0-1)
            
        Returns:
            Delay duration in seconds
        """
        state = self._get_state(key)
        state.attempt += 1
        
        # Update resource state
        if resource_usage is not None:
            state.resource_states.append(resource_usage)
        
        # Select best strategy based on conditions
        strategy = await self._select_strategy(state, resource_usage)
        
        # Calculate delay using selected strategy
        delay = await self._calculate_delay(strategy, state)
        
        # Apply jitter
        jitter = random.uniform(-self.config.jitter, self.config.jitter)
        delay = max(0, delay * (1 + jitter))
        
        # Cap at max delay
        delay = min(delay, self.config.max_delay)
        
        # Update state
        state.last_delay = delay
        state.last_attempt = datetime.utcnow()
        state.delays.append(delay)
        
        return delay
        
    async def record_attempt(self, key: str, success: bool):
        """Record attempt outcome to adjust strategy effectiveness"""
        state = self._get_state(key)
        
        if success:
            state.success_count += 1
        else:
            state.failure_count += 1
            
        state.outcomes.append(success)
        
        # Update strategy effectiveness
        effectiveness = await self._calculate_effectiveness(
            self.current_strategy,
            state
        )
        self.strategy_effectiveness[self.current_strategy] = effectiveness
        
        # Analyze patterns
        await self._analyze_patterns(state)
        
    async def _select_strategy(self,
                             state: BackoffState,
                             resource_usage: Optional[float]) -> BackoffStrategy:
        """Select most appropriate backoff strategy"""
        if not state.delays:  # First attempt
            self.current_strategy = BackoffStrategy.EXPONENTIAL
            return self.current_strategy
            
        # Check resource pressure
        if (resource_usage is not None and 
            resource_usage > self.config.resource_threshold):
            self.current_strategy = BackoffStrategy.RESOURCE_SENSITIVE
            return self.current_strategy
            
        # Check for patterns
        if len(state.outcomes) >= 5:  # Need some history
            pattern = await self._detect_pattern(state)
            if pattern:
                self.current_strategy = BackoffStrategy.PATTERN_BASED
                return self.current_strategy
                
        # Select based on effectiveness
        best_strategy = max(
            self.strategy_effectiveness.items(),
            key=lambda x: x[1]
        )[0]
        
        self.current_strategy = best_strategy
        return best_strategy
        
    async def _calculate_delay(self,
                             strategy: BackoffStrategy,
                             state: BackoffState) -> float:
        """Calculate delay using selected strategy"""
        if strategy == BackoffStrategy.EXPONENTIAL:
            return self.config.initial_delay * (
                self.config.multiplier ** (state.attempt - 1)
            )
            
        elif strategy == BackoffStrategy.FIBONACCI:
            if state.attempt <= 2:
                return self.config.initial_delay
            return state.delays[-1] + state.delays[-2]
            
        elif strategy == BackoffStrategy.DECORRELATED_JITTER:
            if not state.delays:
                return self.config.initial_delay
            return random.uniform(
                self.config.initial_delay,
                state.delays[-1] * 3
            )
            
        elif strategy == BackoffStrategy.RESOURCE_SENSITIVE:
            base_delay = self.config.initial_delay * (
                self.config.multiplier ** (state.attempt - 1)
            )
            if state.resource_states:
                # Increase delay under high resource usage
                resource_factor = state.resource_states[-1]
                return base_delay * (1 + resource_factor)
            return base_delay
            
        elif strategy == BackoffStrategy.PATTERN_BASED:
            pattern = await self._detect_pattern(state)
            if pattern:
                # Use pattern interval as base
                return pattern["interval"] * (
                    1 + (state.attempt - 1) * 0.1
                )
            return self.config.initial_delay
            
        else:  # ADAPTIVE
            # Use weighted combination of other strategies
            delays = await asyncio.gather(
                self._calculate_delay(BackoffStrategy.EXPONENTIAL, state),
                self._calculate_delay(BackoffStrategy.FIBONACCI, state),
                self._calculate_delay(BackoffStrategy.DECORRELATED_JITTER, state)
            )
            weights = [
                self.strategy_effectiveness[BackoffStrategy.EXPONENTIAL],
                self.strategy_effectiveness[BackoffStrategy.FIBONACCI],
                self.strategy_effectiveness[BackoffStrategy.DECORRELATED_JITTER]
            ]
            return sum(d * w for d, w in zip(delays, weights)) / sum(weights)
            
    async def _detect_pattern(self, state: BackoffState) -> Optional[Dict[str, Any]]:
        """Detect patterns in failure/success sequences"""
        if len(state.outcomes) < 5:
            return None
            
        # Look for repeating patterns
        pattern_length = 0
        max_pattern_length = len(state.outcomes) // 2
        
        for length in range(2, max_pattern_length + 1):
            pattern = state.outcomes[-length:]
            next_sequence = state.outcomes[-(length*2):-length]
            
            if pattern == next_sequence:
                pattern_length = length
                break
                
        if pattern_length > 0:
            # Calculate average interval between attempts
            intervals = []
            for i in range(1, len(state.delays)):
                interval = (
                    state.delays[i] - state.delays[i-1]
                ).total_seconds()
                intervals.append(interval)
                
            return {
                "length": pattern_length,
                "pattern": state.outcomes[-pattern_length:],
                "interval": sum(intervals) / len(intervals)
            }
            
        return None
        
    async def _calculate_effectiveness(self,
                                    strategy: BackoffStrategy,
                                    state: BackoffState) -> float:
        """Calculate strategy effectiveness score"""
        if not state.outcomes:
            return 1.0
            
        # Factors to consider
        success_rate = (state.success_count /
                       (state.success_count + state.failure_count))
        
        delay_efficiency = 1.0
        if len(state.delays) >= 2:
            # Check if delays are increasing unnecessarily
            if (state.delays[-1] > state.delays[-2] and
                state.outcomes[-1]):  # Last attempt was successful
                delay_efficiency = 0.8
                
        resource_efficiency = 1.0
        if state.resource_states:
            # Penalize high resource usage
            resource_efficiency = 1.0 - (
                sum(state.resource_states) / len(state.resource_states)
            )
            
        # Combine factors with weights
        return (0.5 * success_rate +
                0.3 * delay_efficiency +
                0.2 * resource_efficiency)
        
    async def _analyze_patterns(self, state: BackoffState):
        """Analyze and record failure/success patterns"""
        pattern = await self._detect_pattern(state)
        if pattern:
            self.pattern_history.append({
                "timestamp": datetime.utcnow(),
                "pattern": pattern,
                "strategy": self.current_strategy
            })
            
    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics and analysis"""
        return {
            "strategy_effectiveness": self.strategy_effectiveness,
            "current_strategy": self.current_strategy.value,
            "pattern_history": [
                {
                    "timestamp": p["timestamp"].isoformat(),
                    "pattern_length": p["pattern"]["length"],
                    "strategy": p["strategy"].value
                }
                for p in self.pattern_history
            ],
            "states": {
                key: {
                    "attempts": state.attempt,
                    "success_rate": (
                        state.success_count /
                        (state.success_count + state.failure_count)
                        if state.success_count + state.failure_count > 0
                        else 0
                    ),
                    "average_delay": (
                        sum(state.delays) / len(state.delays)
                        if state.delays else 0
                    ),
                    "last_attempt": (
                        state.last_attempt.isoformat()
                        if state.last_attempt else None
                    )
                }
                for key, state in self.states.items()
            }
        } 