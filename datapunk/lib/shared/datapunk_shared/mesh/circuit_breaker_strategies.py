from typing import Optional, Dict, Any, List
import structlog
import time
import asyncio
from dataclasses import dataclass
from enum import Enum
from .circuit_breaker_metrics import CircuitBreakerMetrics
from .health_trend_analyzer import HealthTrendAnalyzer, TrendDirection

logger = structlog.get_logger()

class BreakerStrategy(Enum):
    """Circuit breaker strategy types."""
    COUNT_BASED = "count_based"
    RATE_BASED = "rate_based"
    HEALTH_BASED = "health_based"
    ADAPTIVE = "adaptive"

@dataclass
class BreakerStrategyConfig:
    """Configuration for circuit breaker strategies."""
    strategy_type: BreakerStrategy
    failure_threshold: int = 5
    failure_rate_threshold: float = 0.5
    health_threshold: float = 0.3
    window_size: int = 60  # seconds
    min_throughput: int = 10

class CircuitBreakerStrategy:
    """Base class for circuit breaker strategies."""
    
    def __init__(self,
                 config: BreakerStrategyConfig,
                 metrics: CircuitBreakerMetrics):
        self.config = config
        self.metrics = metrics
        self.logger = logger.bind(strategy=config.strategy_type.value)
    
    async def should_open(self, state: Dict[str, Any]) -> bool:
        """Determine if circuit should open."""
        raise NotImplementedError()
    
    async def should_close(self, state: Dict[str, Any]) -> bool:
        """Determine if circuit should close."""
        raise NotImplementedError()

class CountBasedStrategy(CircuitBreakerStrategy):
    """Strategy based on consecutive failures."""
    
    async def should_open(self, state: Dict[str, Any]) -> bool:
        failures = state.get("consecutive_failures", 0)
        return failures >= self.config.failure_threshold
    
    async def should_close(self, state: Dict[str, Any]) -> bool:
        successes = state.get("consecutive_successes", 0)
        return successes >= self.config.failure_threshold

class RateBasedStrategy(CircuitBreakerStrategy):
    """Strategy based on failure rate within window."""
    
    async def should_open(self, state: Dict[str, Any]) -> bool:
        window = state.get("window_stats", {})
        total_requests = sum(window.values())
        
        if total_requests < self.config.min_throughput:
            return False
        
        failure_rate = window.get("failures", 0) / total_requests
        return failure_rate >= self.config.failure_rate_threshold
    
    async def should_close(self, state: Dict[str, Any]) -> bool:
        window = state.get("test_window", {})
        total_requests = sum(window.values())
        
        if total_requests < self.config.min_throughput:
            return False
        
        success_rate = window.get("successes", 0) / total_requests
        return success_rate >= (1 - self.config.failure_rate_threshold)

class HealthBasedStrategy(CircuitBreakerStrategy):
    """Strategy based on service health metrics."""
    
    def __init__(self,
                 config: BreakerStrategyConfig,
                 metrics: CircuitBreakerMetrics,
                 health_analyzer: HealthTrendAnalyzer):
        super().__init__(config, metrics)
        self.health_analyzer = health_analyzer
    
    async def should_open(self, state: Dict[str, Any]) -> bool:
        service = state.get("service")
        if not service:
            return False
        
        trend = await self.health_analyzer.analyze_trend(service, "circuit_breaker")
        
        # Open if health is degrading or below threshold
        return (
            trend.direction == TrendDirection.DEGRADING or
            trend.prediction[-1] < self.config.health_threshold
        )
    
    async def should_close(self, state: Dict[str, Any]) -> bool:
        service = state.get("service")
        if not service:
            return False
        
        trend = await self.health_analyzer.analyze_trend(service, "circuit_breaker")
        
        # Close if health is improving and above threshold
        return (
            trend.direction == TrendDirection.IMPROVING and
            trend.prediction[-1] > self.config.health_threshold
        )

class AdaptiveStrategy(CircuitBreakerStrategy):
    """Strategy that adapts based on multiple factors."""
    
    def __init__(self,
                 config: BreakerStrategyConfig,
                 metrics: CircuitBreakerMetrics,
                 health_analyzer: HealthTrendAnalyzer):
        super().__init__(config, metrics)
        self.health_analyzer = health_analyzer
        self.strategies = {
            BreakerStrategy.COUNT_BASED: CountBasedStrategy(config, metrics),
            BreakerStrategy.RATE_BASED: RateBasedStrategy(config, metrics),
            BreakerStrategy.HEALTH_BASED: HealthBasedStrategy(config, metrics, health_analyzer)
        }
    
    async def select_strategy(self, state: Dict[str, Any]) -> BreakerStrategy:
        """Select best strategy based on current conditions."""
        service = state.get("service")
        if not service:
            return BreakerStrategy.COUNT_BASED
        
        # Check service health trend
        trend = await self.health_analyzer.analyze_trend(service, "circuit_breaker")
        if trend.confidence > 0.8:
            return BreakerStrategy.HEALTH_BASED
        
        # Check request volume
        window = state.get("window_stats", {})
        total_requests = sum(window.values())
        if total_requests >= self.config.min_throughput:
            return BreakerStrategy.RATE_BASED
        
        return BreakerStrategy.COUNT_BASED
    
    async def should_open(self, state: Dict[str, Any]) -> bool:
        strategy_type = await self.select_strategy(state)
        strategy = self.strategies[strategy_type]
        
        self.logger.info("selected_strategy",
                        strategy=strategy_type.value,
                        service=state.get("service"))
        
        return await strategy.should_open(state)
    
    async def should_close(self, state: Dict[str, Any]) -> bool:
        strategy_type = await self.select_strategy(state)
        strategy = self.strategies[strategy_type]
        
        self.logger.info("selected_strategy",
                        strategy=strategy_type.value,
                        service=state.get("service"))
        
        return await strategy.should_close(state) 