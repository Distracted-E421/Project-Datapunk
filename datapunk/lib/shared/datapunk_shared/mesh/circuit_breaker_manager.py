from typing import Dict, Optional
import structlog
import asyncio
from dataclasses import dataclass
from .circuit_breaker_strategies import (
    BreakerStrategy,
    BreakerStrategyConfig,
    CircuitBreakerStrategy,
    AdaptiveStrategy
)
from .circuit_breaker_metrics import CircuitBreakerMetrics
from .health_trend_analyzer import HealthTrendAnalyzer

logger = structlog.get_logger()

@dataclass
class CircuitState:
    """Circuit breaker state for a service."""
    service: str
    strategy: CircuitBreakerStrategy
    is_open: bool = False
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    window_stats: Dict[str, int] = None
    last_failure_time: float = 0
    last_state_change: float = 0

class CircuitBreakerManager:
    """Manages circuit breakers for multiple services."""
    
    def __init__(self,
                 metrics: CircuitBreakerMetrics,
                 health_analyzer: HealthTrendAnalyzer):
        self.metrics = metrics
        self.health_analyzer = health_analyzer
        self.circuits: Dict[str, CircuitState] = {}
        self.logger = logger.bind(component="circuit_manager")
        
        # Start maintenance task
        asyncio.create_task(self._maintenance_loop())
    
    async def register_service(self,
                             service: str,
                             strategy_type: BreakerStrategy = BreakerStrategy.ADAPTIVE,
                             config: Optional[BreakerStrategyConfig] = None) -> None:
        """Register a service for circuit breaking."""
        if service in self.circuits:
            return
        
        config = config or BreakerStrategyConfig(strategy_type=strategy_type)
        
        if strategy_type == BreakerStrategy.ADAPTIVE:
            strategy = AdaptiveStrategy(config, self.metrics, self.health_analyzer)
        else:
            strategy = CircuitBreakerStrategy(config, self.metrics)
        
        self.circuits[service] = CircuitState(
            service=service,
            strategy=strategy,
            window_stats={"successes": 0, "failures": 0}
        )
        
        self.logger.info("service_registered",
                        service=service,
                        strategy=strategy_type.value)
    
    async def check_state(self, service: str) -> bool:
        """Check if circuit is closed for service."""
        circuit = self.circuits.get(service)
        if not circuit:
            return True  # Default to closed if not registered
        
        return not circuit.is_open
    
    async def record_success(self, service: str) -> None:
        """Record successful request."""
        circuit = self.circuits.get(service)
        if not circuit:
            return
        
        circuit.consecutive_failures = 0
        circuit.consecutive_successes += 1
        circuit.window_stats["successes"] = circuit.window_stats.get("successes", 0) + 1
        
        if circuit.is_open:
            # Check if circuit should close
            state = self._get_circuit_state(circuit)
            if await circuit.strategy.should_close(state):
                await self._close_circuit(circuit)
    
    async def record_failure(self, service: str) -> None:
        """Record failed request."""
        circuit = self.circuits.get(service)
        if not circuit:
            return
        
        circuit.consecutive_failures += 1
        circuit.consecutive_successes = 0
        circuit.window_stats["failures"] = circuit.window_stats.get("failures", 0) + 1
        
        if not circuit.is_open:
            # Check if circuit should open
            state = self._get_circuit_state(circuit)
            if await circuit.strategy.should_open(state):
                await self._open_circuit(circuit)
    
    async def _maintenance_loop(self):
        """Periodic maintenance of circuit states."""
        while True:
            try:
                for circuit in self.circuits.values():
                    # Reset window stats periodically
                    circuit.window_stats = {"successes": 0, "failures": 0}
                    
                    # Update metrics
                    self.metrics.update_circuit_state(
                        circuit.service,
                        "open" if circuit.is_open else "closed"
                    )
            except Exception as e:
                self.logger.error("maintenance_failed", error=str(e))
            
            await asyncio.sleep(60)  # Run every minute
    
    def _get_circuit_state(self, circuit: CircuitState) -> Dict:
        """Get current circuit state for strategy evaluation."""
        return {
            "service": circuit.service,
            "consecutive_failures": circuit.consecutive_failures,
            "consecutive_successes": circuit.consecutive_successes,
            "window_stats": circuit.window_stats,
            "last_failure_time": circuit.last_failure_time,
            "last_state_change": circuit.last_state_change
        }
    
    async def _open_circuit(self, circuit: CircuitState) -> None:
        """Open circuit breaker."""
        circuit.is_open = True
        circuit.last_state_change = time.time()
        
        self.logger.warning("circuit_opened",
                          service=circuit.service,
                          failures=circuit.consecutive_failures)
        
        self.metrics.record_state_change(
            circuit.service,
            "open",
            circuit.consecutive_failures
        )
    
    async def _close_circuit(self, circuit: CircuitState) -> None:
        """Close circuit breaker."""
        circuit.is_open = False
        circuit.last_state_change = time.time()
        circuit.consecutive_failures = 0
        
        self.logger.info("circuit_closed",
                        service=circuit.service)
        
        self.metrics.record_state_change(
            circuit.service,
            "closed",
            circuit.consecutive_successes
        ) 