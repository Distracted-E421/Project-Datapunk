import unittest
from datetime import datetime, timedelta
import tempfile
import os
import time
from unittest.mock import Mock, patch

from ..src.storage.index.stats import (
    IndexStats,
    IndexUsageStats,
    IndexSizeStats,
    IndexConditionStats,
    StatisticsStore
)
from ..src.storage.index.triggers import (
    OptimizationTrigger,
    TriggerConfig,
    TriggerType,
    TriggerEvent
)

class TestOptimizationTrigger(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stats.db")
        
        # Initialize store and trigger
        self.store = StatisticsStore(self.db_path)
        self.config = TriggerConfig(
            check_interval_seconds=1,  # Fast checks for testing
            cooldown_minutes=0  # No cooldown for testing
        )
        self.trigger = OptimizationTrigger(self.store, self.config)
        
        # Create sample stats
        self.sample_stats = IndexStats(
            index_name="test_index",
            table_name="test_table",
            index_type="btree",
            created_at=datetime.now(),
            usage=IndexUsageStats(
                total_reads=1000,
                total_writes=500,
                avg_read_time_ms=50.0,
                avg_write_time_ms=100.0,
                cache_hits=800,
                cache_misses=200
            ),
            size=IndexSizeStats(
                total_entries=10000,
                depth=4,
                size_bytes=102400,
                fragmentation_ratio=0.1
            ),
            condition=IndexConditionStats(
                condition_string="status = 'active'",
                selectivity=0.3,
                false_positive_rate=0.1,
                evaluation_time_ms=0.3
            )
        )
        
    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
        
        # Stop monitoring if active
        self.trigger.stop_monitoring()
        
    def test_fragmentation_trigger(self):
        # Create stats with high fragmentation
        stats = self.sample_stats
        stats.size.fragmentation_ratio = 0.4  # Above threshold
        self.store.save_stats(stats)
        
        # Check triggers
        events = self.trigger.check_triggers("test_index")
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].trigger_type, TriggerType.FRAGMENTATION)
        self.assertGreater(events[0].current_value, events[0].threshold)
        
    def test_performance_trigger(self):
        # Create stats with slow performance
        stats = self.sample_stats
        stats.usage.avg_read_time_ms = 150.0  # Above threshold
        stats.usage.avg_write_time_ms = 250.0  # Above threshold
        self.store.save_stats(stats)
        
        # Check triggers
        events = self.trigger.check_triggers("test_index")
        
        self.assertEqual(len(events), 2)  # Both read and write triggers
        self.assertTrue(any(e.trigger_type == TriggerType.PERFORMANCE for e in events))
        
    def test_cache_trigger(self):
        # Create stats with poor cache performance
        stats = self.sample_stats
        stats.usage.cache_hits = 500
        stats.usage.cache_misses = 500  # 50% hit ratio
        self.store.save_stats(stats)
        
        # Check triggers
        events = self.trigger.check_triggers("test_index")
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].trigger_type, TriggerType.CACHE)
        
    def test_size_trigger(self):
        # Create historical data showing rapid growth
        base_time = datetime.now() - timedelta(days=1)
        
        # Initial stats
        stats = self.sample_stats
        stats.created_at = base_time
        stats.size.total_entries = 10000
        self.store.save_stats(stats)
        
        # Updated stats showing growth
        stats.created_at = datetime.now()
        stats.size.total_entries = 20000  # 100% growth
        self.store.save_stats(stats)
        
        # Check triggers
        events = self.trigger.check_triggers("test_index")
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].trigger_type, TriggerType.SIZE)
        
    def test_error_rate_trigger(self):
        # Create stats with high false positive rate
        stats = self.sample_stats
        stats.condition.false_positive_rate = 0.3  # Above threshold
        self.store.save_stats(stats)
        
        # Check triggers
        events = self.trigger.check_triggers("test_index")
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].trigger_type, TriggerType.ERROR_RATE)
        
    def test_optimization_actions(self):
        # Create multiple trigger events
        events = [
            TriggerEvent(
                trigger_type=TriggerType.FRAGMENTATION,
                index_name="test_index",
                timestamp=datetime.now(),
                current_value=0.4,
                threshold=0.3,
                message="High fragmentation"
            ),
            TriggerEvent(
                trigger_type=TriggerType.PERFORMANCE,
                index_name="test_index",
                timestamp=datetime.now(),
                current_value=150.0,
                threshold=100.0,
                message="Slow reads"
            )
        ]
        
        # Get optimization actions
        actions = self.trigger.get_optimization_actions(events)
        
        self.assertEqual(len(actions), 2)
        self.assertTrue(all(callable(action) for action in actions))
        
    def test_monitoring_thread(self):
        # Mock optimization methods
        self.trigger._rebuild_index = Mock()
        self.trigger._analyze_index = Mock()
        
        # Create stats that will trigger optimizations
        stats = self.sample_stats
        stats.size.fragmentation_ratio = 0.4
        stats.usage.avg_read_time_ms = 150.0
        self.store.save_stats(stats)
        
        # Start monitoring
        self.trigger.start_monitoring()
        
        # Wait for monitoring cycle
        time.sleep(2)
        
        # Verify optimizations were triggered
        self.assertTrue(self.trigger._rebuild_index.called or 
                       self.trigger._analyze_index.called)
        
    def test_cooldown_period(self):
        # Configure cooldown
        self.trigger.config.cooldown_minutes = 60
        
        # Record optimization
        self.trigger._last_optimization["test_index"] = datetime.now()
        
        # Try to optimize
        result = self.trigger.execute_optimizations("test_index")
        
        # Should not optimize during cooldown
        self.assertFalse(result)
        
    def test_optimization_error_handling(self):
        # Create failing action
        def failing_action():
            raise Exception("Optimization failed")
            
        # Create trigger event
        event = TriggerEvent(
            trigger_type=TriggerType.FRAGMENTATION,
            index_name="test_index",
            timestamp=datetime.now(),
            current_value=0.4,
            threshold=0.3,
            message="Test event"
        )
        
        # Mock get_optimization_actions
        with patch.object(
            self.trigger,
            'get_optimization_actions',
            return_value=[failing_action]
        ):
            # Execute optimization
            result = self.trigger.execute_optimizations("test_index")
            
            # Should handle error and return False
            self.assertFalse(result)
            
    def test_trigger_check_interval(self):
        # Check trigger
        self.trigger.check_triggers("test_index")
        
        # Immediate check should be skipped
        events = self.trigger.check_triggers("test_index")
        self.assertEqual(len(events), 0)
        
        # Wait for interval
        time.sleep(1)
        
        # Should check again
        stats = self.sample_stats
        stats.size.fragmentation_ratio = 0.4
        self.store.save_stats(stats)
        
        events = self.trigger.check_triggers("test_index")
        self.assertEqual(len(events), 1) 