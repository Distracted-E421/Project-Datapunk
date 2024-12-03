"""
Adaptive Timeout Management

Implements dynamic timeout adjustment based on service performance metrics.
Uses statistical analysis to optimize timeout values and reduce false positives.
"""

from typing import Optional, Dict, List, Tuple
from enum import Enum
import structlog
import numpy as np
from datetime import datetime, timedelta
from collections import deque

logger = structlog.get_logger()

class TimeoutStrategy(Enum):
    """Available timeout adjustment strategies"""
    PERCENTILE = "percentile"  # Use percentile of response times
    ADAPTIVE = "adaptive"      # Dynamically adjust based on conditions
    HYBRID = "hybrid"         # Combine multiple strategies

class TimeoutConfig:
    """Configuration for timeout management"""
    def __init__(self,
                 min_timeout_ms: float = 100.0,
                 max_timeout_ms: float = 30000.0,
                 initial_timeout_ms: float = 1000.0,
                 strategy: TimeoutStrategy = TimeoutStrategy.HYBRID,
                 window_size: int = 100,
                 percentile: float = 95.0,
                 adjustment_factor: float = 1.5):
        self.min_timeout_ms = min_timeout_ms
        self.max_timeout_ms = max_timeout_ms
        self.initial_timeout_ms = initial_timeout_ms
        self.strategy = strategy
        self.window_size = window_size
        self.percentile = percentile
        self.adjustment_factor = adjustment_factor

class ResponseTimeTracker:
    """Tracks response times for timeout calculation"""
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.response_times = deque(maxlen=window_size)
        self.success_times = deque(maxlen=window_size)
        self.failure_times = deque(maxlen=window_size)
        
    def add_response_time(self,
                         response_time_ms: float,
                         is_success: bool = True):
        """Add new response time measurement"""
        self.response_times.append(response_time_ms)
        if is_success:
            self.success_times.append(response_time_ms)
        else:
            self.failure_times.append(response_time_ms)
            
    def get_percentile(self, percentile: float) -> float:
        """Calculate percentile of response times"""
        if not self.response_times:
            return 0.0
        return float(np.percentile(self.response_times, percentile))
        
    def get_success_rate(self) -> float:
        """Calculate success rate"""
        total = len(self.success_times) + len(self.failure_times)
        if total == 0:
            return 1.0
        return len(self.success_times) / total
        
    def get_stats(self) -> Dict[str, float]:
        """Get response time statistics"""
        if not self.response_times:
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "success_rate": 1.0
            }
            
        return {
            "mean": float(np.mean(self.response_times)),
            "std": float(np.std(self.response_times)),
            "min": float(np.min(self.response_times)),
            "max": float(np.max(self.response_times)),
            "success_rate": self.get_success_rate()
        }

class AdaptiveTimeout:
    """
    Manages dynamic timeout adjustments based on service performance.
    
    Features:
    - Multiple timeout strategies
    - Response time tracking
    - Success rate monitoring
    - Gradual timeout adjustment
    - Outlier detection
    """
    
    def __init__(self,
                 config: Optional[TimeoutConfig] = None,
                 metrics_client = None):
        self.config = config or TimeoutConfig()
        self.metrics = metrics_client
        self.logger = logger.bind(component="adaptive_timeout")
        
        # Initialize trackers
        self.tracker = ResponseTimeTracker(
            window_size=self.config.window_size
        )
        
        # Current timeout value
        self.current_timeout_ms = self.config.initial_timeout_ms
        
        # Track adjustment history
        self.adjustment_history = deque(maxlen=100)
        
    async def record_response_time(self,
                                 response_time_ms: float,
                                 is_success: bool = True):
        """Record response time measurement"""
        self.tracker.add_response_time(response_time_ms, is_success)
        
        if self.metrics:
            await self.metrics.gauge(
                "circuit_breaker_response_time",
                response_time_ms,
                {"success": str(is_success)}
            )
            
    async def get_timeout(self) -> float:
        """Get current timeout value"""
        if self.config.strategy == TimeoutStrategy.PERCENTILE:
            timeout = self._calculate_percentile_timeout()
        elif self.config.strategy == TimeoutStrategy.ADAPTIVE:
            timeout = await self._calculate_adaptive_timeout()
        else:  # HYBRID
            timeout = await self._calculate_hybrid_timeout()
            
        # Apply bounds
        timeout = max(self.config.min_timeout_ms,
                     min(self.config.max_timeout_ms, timeout))
                     
        # Record adjustment if changed
        if timeout != self.current_timeout_ms:
            self.adjustment_history.append(
                (datetime.utcnow(), self.current_timeout_ms, timeout)
            )
            self.current_timeout_ms = timeout
            
            if self.metrics:
                await self.metrics.gauge(
                    "circuit_breaker_timeout",
                    timeout
                )
                
        return timeout
        
    def _calculate_percentile_timeout(self) -> float:
        """Calculate timeout using percentile strategy"""
        base_timeout = self.tracker.get_percentile(
            self.config.percentile
        )
        
        if base_timeout == 0:
            return self.current_timeout_ms
            
        # Add buffer for variance
        return base_timeout * self.config.adjustment_factor
        
    async def _calculate_adaptive_timeout(self) -> float:
        """Calculate timeout using adaptive strategy"""
        stats = self.tracker.get_stats()
        
        if stats["mean"] == 0:
            return self.current_timeout_ms
            
        # Start with mean + 2 standard deviations
        base_timeout = stats["mean"] + (2 * stats["std"])
        
        # Adjust based on success rate
        success_rate = stats["success_rate"]
        if success_rate < 0.95:  # High failure rate
            # Increase timeout to reduce failures
            base_timeout *= (2 - success_rate)
        elif success_rate > 0.99:  # Very successful
            # Gradually reduce timeout
            base_timeout *= 0.95
            
        return base_timeout
        
    async def _calculate_hybrid_timeout(self) -> float:
        """Calculate timeout using hybrid strategy"""
        percentile_timeout = self._calculate_percentile_timeout()
        adaptive_timeout = await self._calculate_adaptive_timeout()
        
        # Use weighted combination
        stats = self.tracker.get_stats()
        success_rate = stats["success_rate"]
        
        # Weight adaptive timeout more heavily when success rate is low
        adaptive_weight = 1 - success_rate
        percentile_weight = success_rate
        
        return (
            (adaptive_timeout * adaptive_weight) +
            (percentile_timeout * percentile_weight)
        )
        
    def get_timeout_metrics(self) -> Dict[str, float]:
        """Get current timeout metrics"""
        stats = self.tracker.get_stats()
        
        metrics = {
            "current_timeout": self.current_timeout_ms,
            "success_rate": stats["success_rate"],
            "mean_response_time": stats["mean"],
            "max_response_time": stats["max"],
            "std_response_time": stats["std"]
        }
        
        # Add recent adjustments
        if self.adjustment_history:
            last_adjustment = self.adjustment_history[-1]
            metrics["last_adjustment_time"] = last_adjustment[0].timestamp()
            metrics["last_adjustment_from"] = last_adjustment[1]
            metrics["last_adjustment_to"] = last_adjustment[2]
            
        return metrics 