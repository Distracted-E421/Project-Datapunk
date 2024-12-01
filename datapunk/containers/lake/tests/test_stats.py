import unittest
from datetime import datetime, timedelta
import os
import tempfile
import json
from typing import Dict, Any

from ..src.storage.index.stats import (
    IndexStats,
    IndexUsageStats,
    IndexSizeStats,
    IndexConditionStats,
    IndexMaintenanceStats,
    StatisticsStore,
    StatisticsManager
)

class TestStatisticsStore(unittest.TestCase):
    def setUp(self):
        # Use temporary file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stats.db")
        self.store = StatisticsStore(self.db_path)
        
        # Create sample stats
        self.sample_stats = IndexStats(
            index_name="test_index",
            table_name="test_table",
            index_type="btree",
            created_at=datetime.now(),
            usage=IndexUsageStats(
                total_reads=100,
                total_writes=50,
                avg_read_time_ms=0.5,
                avg_write_time_ms=1.0,
                cache_hits=80,
                cache_misses=20,
                last_used=datetime.now()
            ),
            size=IndexSizeStats(
                total_entries=1000,
                depth=3,
                size_bytes=10240,
                fragmentation_ratio=0.1,
                last_compacted=datetime.now()
            ),
            condition=IndexConditionStats(
                condition_string="age > 30",
                selectivity=0.4,
                false_positive_rate=0.1,
                evaluation_time_ms=0.2,
                last_optimized=datetime.now()
            )
        )
        
    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
        
    def test_save_and_get_stats(self):
        # Save stats
        self.store.save_stats(self.sample_stats)
        
        # Retrieve stats
        retrieved = self.store.get_latest_stats("test_index")
        
        # Verify core attributes
        self.assertEqual(retrieved.index_name, "test_index")
        self.assertEqual(retrieved.table_name, "test_table")
        self.assertEqual(retrieved.index_type, "btree")
        
        # Verify nested objects
        self.assertEqual(retrieved.usage.total_reads, 100)
        self.assertEqual(retrieved.size.total_entries, 1000)
        self.assertEqual(retrieved.condition.selectivity, 0.4)
        
    def test_save_snapshot(self):
        snapshot_data = {
            "metric1": 100,
            "metric2": "value"
        }
        
        # Save snapshot
        self.store.save_snapshot(
            "test_index",
            "test_snapshot",
            snapshot_data
        )
        
        # Retrieve snapshots
        snapshots = self.store.get_snapshots(
            "test_index",
            "test_snapshot"
        )
        
        self.assertEqual(len(snapshots), 1)
        self.assertEqual(snapshots[0]["data"], snapshot_data)
        
    def test_get_stats_history(self):
        # Save multiple stats entries
        for i in range(3):
            stats = self.sample_stats
            stats.usage.total_reads += i * 100
            self.store.save_stats(stats)
            
        # Get history
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now() + timedelta(days=1)
        
        history = self.store.get_stats_history(
            "test_index",
            start_time,
            end_time
        )
        
        self.assertEqual(len(history), 3)
        self.assertTrue(
            all(isinstance(stats, IndexStats) for stats in history)
        )
        
    def test_cleanup_old_stats(self):
        # Save old and new stats
        old_stats = self.sample_stats
        old_stats.created_at = datetime.now() - timedelta(days=40)
        self.store.save_stats(old_stats)
        
        new_stats = self.sample_stats
        new_stats.created_at = datetime.now()
        self.store.save_stats(new_stats)
        
        # Clean up old stats
        self.store.cleanup_old_stats(days_to_keep=30)
        
        # Verify only new stats remain
        history = self.store.get_stats_history(
            "test_index",
            datetime.now() - timedelta(days=60),
            datetime.now()
        )
        
        self.assertEqual(len(history), 1)
        
class TestStatisticsManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stats.db")
        self.store = StatisticsStore(self.db_path)
        self.manager = StatisticsManager(self.store)
        
        # Create sample stats
        self.sample_stats = IndexStats(
            index_name="test_index",
            table_name="test_table",
            index_type="btree",
            created_at=datetime.now(),
            usage=IndexUsageStats(
                total_reads=1000,
                total_writes=500,
                avg_read_time_ms=1.0,
                avg_write_time_ms=2.0,
                cache_hits=800,
                cache_misses=200
            ),
            size=IndexSizeStats(
                total_entries=10000,
                depth=4,
                size_bytes=102400,
                fragmentation_ratio=0.2
            ),
            condition=IndexConditionStats(
                condition_string="status = 'active'",
                selectivity=0.3,
                false_positive_rate=0.15,
                evaluation_time_ms=0.3
            )
        )
        
    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
        
    def test_update_stats(self):
        # Update stats
        self.manager.update_stats(self.sample_stats)
        
        # Verify stats were saved
        retrieved = self.store.get_latest_stats("test_index")
        self.assertEqual(retrieved.index_name, "test_index")
        
        # Verify snapshots were created
        size_snapshots = self.store.get_snapshots(
            "test_index",
            "size"
        )
        perf_snapshots = self.store.get_snapshots(
            "test_index",
            "performance"
        )
        condition_snapshots = self.store.get_snapshots(
            "test_index",
            "condition"
        )
        
        self.assertEqual(len(size_snapshots), 1)
        self.assertEqual(len(perf_snapshots), 1)
        self.assertEqual(len(condition_snapshots), 1)
        
    def test_analyze_trends(self):
        # Save historical stats
        for i in range(7):
            stats = self.sample_stats
            stats.size.total_entries += i * 1000
            stats.usage.avg_read_time_ms += i * 0.1
            stats.created_at = datetime.now() - timedelta(days=6-i)
            self.manager.update_stats(stats)
            
        # Analyze trends
        trends = self.manager.analyze_trends("test_index", days=7)
        
        self.assertIn("growth_rate_per_day", trends)
        self.assertIn("avg_read_time_trend", trends)
        self.assertIn("avg_write_time_trend", trends)
        self.assertIn("maintenance_frequency", trends)
        self.assertIn("needs_optimization", trends)
        
    def test_needs_optimization(self):
        # Test case requiring optimization
        stats = self.sample_stats
        stats.size.fragmentation_ratio = 0.4  # Above threshold
        self.assertTrue(self.manager._needs_optimization(stats))
        
        # Test case not requiring optimization
        stats.size.fragmentation_ratio = 0.1
        stats.usage.avg_read_time_ms = 50
        stats.condition.false_positive_rate = 0.1
        self.assertFalse(self.manager._needs_optimization(stats))
        
    def test_snapshot_interval(self):
        # First update should create snapshots
        self.manager.update_stats(self.sample_stats)
        initial_snapshots = self.store.get_snapshots(
            "test_index",
            "size"
        )
        
        # Immediate update should not create new snapshots
        self.manager.update_stats(self.sample_stats)
        current_snapshots = self.store.get_snapshots(
            "test_index",
            "size"
        )
        
        self.assertEqual(
            len(initial_snapshots),
            len(current_snapshots)
        ) 