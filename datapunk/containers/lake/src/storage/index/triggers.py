from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum
import threading
import time

from .stats import (
    IndexStats,
    StatisticsStore,
    StatisticsManager
)
from .optimizer import ConditionOptimizer

logger = logging.getLogger(__name__)

class TriggerType(Enum):
    """Types of optimization triggers."""
    FRAGMENTATION = "fragmentation"
    PERFORMANCE = "performance"
    SELECTIVITY = "selectivity"
    CACHE = "cache"
    SIZE = "size"
    ERROR_RATE = "error_rate"

@dataclass
class TriggerConfig:
    """Configuration for optimization triggers."""
    fragmentation_threshold: float = 0.3
    read_time_threshold_ms: float = 100.0
    write_time_threshold_ms: float = 200.0
    cache_hit_ratio_threshold: float = 0.7
    size_growth_rate_threshold: float = 0.5  # 50% per day
    false_positive_threshold: float = 0.2
    check_interval_seconds: int = 300  # 5 minutes
    min_sample_size: int = 100
    cooldown_minutes: int = 60

@dataclass
class TriggerEvent:
    """Represents an optimization trigger event."""
    trigger_type: TriggerType
    index_name: str
    timestamp: datetime
    current_value: float
    threshold: float
    message: str

class OptimizationTrigger:
    """Monitors index statistics and triggers optimizations."""
    
    def __init__(
        self,
        store: StatisticsStore,
        config: Optional[TriggerConfig] = None,
        optimizer: Optional[ConditionOptimizer] = None
    ):
        self.store = store
        self.config = config or TriggerConfig()
        self.optimizer = optimizer or ConditionOptimizer()
        
        self._triggers: Dict[str, List[TriggerEvent]] = {}
        self._last_check: Dict[str, datetime] = {}
        self._last_optimization: Dict[str, datetime] = {}
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        
    def start_monitoring(self):
        """Start the monitoring thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
            
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("Started index optimization monitoring")
        
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        if self._monitor_thread:
            self._stop_event.set()
            self._monitor_thread.join()
            logger.info("Stopped index optimization monitoring")
            
    def check_triggers(self, index_name: str) -> List[TriggerEvent]:
        """Check all triggers for an index."""
        stats = self.store.get_latest_stats(index_name)
        if not stats:
            return []
            
        events = []
        
        # Check fragmentation
        if self._should_check_trigger(index_name, TriggerType.FRAGMENTATION):
            if stats.size.fragmentation_ratio > self.config.fragmentation_threshold:
                events.append(self._create_event(
                    TriggerType.FRAGMENTATION,
                    index_name,
                    stats.size.fragmentation_ratio,
                    self.config.fragmentation_threshold,
                    "High fragmentation detected"
                ))
                
        # Check performance
        if self._should_check_trigger(index_name, TriggerType.PERFORMANCE):
            if stats.usage.avg_read_time_ms > self.config.read_time_threshold_ms:
                events.append(self._create_event(
                    TriggerType.PERFORMANCE,
                    index_name,
                    stats.usage.avg_read_time_ms,
                    self.config.read_time_threshold_ms,
                    "Slow read performance detected"
                ))
                
            if stats.usage.avg_write_time_ms > self.config.write_time_threshold_ms:
                events.append(self._create_event(
                    TriggerType.PERFORMANCE,
                    index_name,
                    stats.usage.avg_write_time_ms,
                    self.config.write_time_threshold_ms,
                    "Slow write performance detected"
                ))
                
        # Check cache performance
        if self._should_check_trigger(index_name, TriggerType.CACHE):
            total = stats.usage.cache_hits + stats.usage.cache_misses
            if total > self.config.min_sample_size:
                hit_ratio = stats.usage.cache_hits / total
                if hit_ratio < self.config.cache_hit_ratio_threshold:
                    events.append(self._create_event(
                        TriggerType.CACHE,
                        index_name,
                        hit_ratio,
                        self.config.cache_hit_ratio_threshold,
                        "Low cache hit ratio detected"
                    ))
                    
        # Check size growth
        if self._should_check_trigger(index_name, TriggerType.SIZE):
            growth_rate = self._calculate_growth_rate(index_name)
            if growth_rate > self.config.size_growth_rate_threshold:
                events.append(self._create_event(
                    TriggerType.SIZE,
                    index_name,
                    growth_rate,
                    self.config.size_growth_rate_threshold,
                    "Rapid size growth detected"
                ))
                
        # Check condition effectiveness
        if (stats.condition and 
            self._should_check_trigger(index_name, TriggerType.ERROR_RATE)):
            if stats.condition.false_positive_rate > self.config.false_positive_threshold:
                events.append(self._create_event(
                    TriggerType.ERROR_RATE,
                    index_name,
                    stats.condition.false_positive_rate,
                    self.config.false_positive_threshold,
                    "High false positive rate detected"
                ))
                
        # Store trigger events
        if events:
            self._triggers.setdefault(index_name, []).extend(events)
            
        return events
        
    def get_optimization_actions(
        self,
        events: List[TriggerEvent]
    ) -> List[Callable[[], None]]:
        """Get optimization actions for trigger events."""
        actions = []
        
        for event in events:
            if event.trigger_type == TriggerType.FRAGMENTATION:
                actions.append(lambda: self._rebuild_index(event.index_name))
                
            elif event.trigger_type == TriggerType.PERFORMANCE:
                actions.append(lambda: self._analyze_index(event.index_name))
                
            elif event.trigger_type == TriggerType.CACHE:
                actions.append(lambda: self._optimize_cache(event.index_name))
                
            elif event.trigger_type == TriggerType.SIZE:
                actions.append(lambda: self._compact_index(event.index_name))
                
            elif event.trigger_type == TriggerType.ERROR_RATE:
                actions.append(lambda: self._optimize_condition(event.index_name))
                
        return actions
        
    def execute_optimizations(self, index_name: str) -> bool:
        """Execute optimizations if needed."""
        if not self._can_optimize(index_name):
            return False
            
        events = self.check_triggers(index_name)
        if not events:
            return False
            
        actions = self.get_optimization_actions(events)
        success = True
        
        for action in actions:
            try:
                action()
            except Exception as e:
                logger.error(f"Optimization failed: {str(e)}")
                success = False
                
        if success:
            self._last_optimization[index_name] = datetime.now()
            
        return success
        
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                # Get all indexes
                stats_list = self.store.get_latest_stats("*")
                
                for stats in stats_list:
                    self.execute_optimizations(stats.index_name)
                    
            except Exception as e:
                logger.error(f"Monitoring error: {str(e)}")
                
            time.sleep(self.config.check_interval_seconds)
            
    def _should_check_trigger(
        self,
        index_name: str,
        trigger_type: TriggerType
    ) -> bool:
        """Check if we should evaluate a trigger."""
        last_check = self._last_check.get((index_name, trigger_type))
        if not last_check:
            return True
            
        return (datetime.now() - last_check).total_seconds() >= self.config.check_interval_seconds
        
    def _can_optimize(self, index_name: str) -> bool:
        """Check if optimization is allowed."""
        last_opt = self._last_optimization.get(index_name)
        if not last_opt:
            return True
            
        return (datetime.now() - last_opt).total_seconds() >= (self.config.cooldown_minutes * 60)
        
    def _create_event(
        self,
        trigger_type: TriggerType,
        index_name: str,
        current_value: float,
        threshold: float,
        message: str
    ) -> TriggerEvent:
        """Create a trigger event."""
        return TriggerEvent(
            trigger_type=trigger_type,
            index_name=index_name,
            timestamp=datetime.now(),
            current_value=current_value,
            threshold=threshold,
            message=message
        )
        
    def _calculate_growth_rate(self, index_name: str) -> float:
        """Calculate daily growth rate."""
        history = self.store.get_stats_history(
            index_name,
            datetime.now() - timedelta(days=1),
            datetime.now()
        )
        
        if len(history) < 2:
            return 0.0
            
        initial_size = history[0].size.total_entries
        final_size = history[-1].size.total_entries
        
        if initial_size == 0:
            return 0.0
            
        return (final_size - initial_size) / initial_size
        
    def _rebuild_index(self, index_name: str):
        """Rebuild an index to reduce fragmentation."""
        logger.info(f"Rebuilding index {index_name}")
        # Implementation depends on specific index type
        
    def _analyze_index(self, index_name: str):
        """Analyze index for performance optimization."""
        logger.info(f"Analyzing index {index_name}")
        # Implementation depends on specific index type
        
    def _optimize_cache(self, index_name: str):
        """Optimize index cache settings."""
        logger.info(f"Optimizing cache for {index_name}")
        # Implementation depends on specific index type
        
    def _compact_index(self, index_name: str):
        """Compact index to reduce size."""
        logger.info(f"Compacting index {index_name}")
        # Implementation depends on specific index type
        
    def _optimize_condition(self, index_name: str):
        """Optimize index condition."""
        logger.info(f"Optimizing condition for {index_name}")
        stats = self.store.get_latest_stats(index_name)
        if stats and stats.condition:
            # Use condition optimizer
            optimized, _ = self.optimizer.optimize(stats.condition)
            # Implementation to apply optimized condition 