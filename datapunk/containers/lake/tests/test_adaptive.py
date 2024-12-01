import unittest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime, timedelta
import time

from ..src.storage.index.adaptive import (
    AdaptiveIndexManager,
    PartitionStrategy,
    PartitionInfo,
    QueryPattern
)
from ..src.storage.index.stats import (
    StatisticsStore,
    IndexStats,
    IndexUsageStats,
    IndexSizeStats
)
from ..src.storage.index.manager import IndexManager
from ..src.storage.index.optimizer import IndexOptimizer

class TestAdaptiveIndexing(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_stats.db"
        self.config_path = Path(self.temp_dir) / "adaptive_config.json"
        
        # Initialize components
        self.store = StatisticsStore(self.db_path)
        self.manager = IndexManager(self.store)
        self.optimizer = IndexOptimizer(self.store)
        
        # Create test configuration
        config = {
            "partition_size_threshold": 1024 * 1024,  # 1MB for testing
            "max_partitions_per_index": 10,
            "hot_data_threshold_days": 1,
            "pattern_expiry_days": 7,
            "min_pattern_frequency": 2,
            "score_weights": {
                "query_frequency": 0.4,
                "data_size": 0.2,
                "maintenance_cost": 0.2,
                "access_pattern": 0.2
            },
            "maintenance_window": {
                "start_hour": 1,
                "end_hour": 5
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
            
        self.adaptive = AdaptiveIndexManager(
            self.store,
            self.manager,
            self.optimizer,
            self.config_path
        )
        
        # Create test data
        self._create_test_data()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def _create_test_data(self):
        """Create test indexes and statistics."""
        base_time = datetime.now() - timedelta(days=1)
        
        # Create test indexes
        for i in range(5):
            stats = IndexStats(
                index_name=f"index_{i}",
                table_name="test_table",
                index_type="btree",
                created_at=base_time,
                usage=IndexUsageStats(
                    total_reads=1000 * (i + 1),
                    total_writes=500,
                    avg_read_time_ms=1.0,
                    avg_write_time_ms=2.0,
                    cache_hits=800,
                    cache_misses=200
                ),
                size=IndexSizeStats(
                    total_entries=10000 * (i + 1),
                    depth=4,
                    size_bytes=102400 * (i + 1),
                    fragmentation_ratio=0.1 * (i + 1)
                )
            )
            self.store.save_stats(stats)
            
    def test_query_pattern_analysis(self):
        """Test query pattern analysis."""
        # Add query patterns
        self.adaptive.analyze_query_pattern(
            query_type="SELECT",
            predicates=["time > 2023-01-01"],
            execution_time=1.0,
            affected_indexes={"index_0"}
        )
        
        self.adaptive.analyze_query_pattern(
            query_type="SELECT",
            predicates=["time > 2023-01-01"],
            execution_time=1.5,
            affected_indexes={"index_0"}
        )
        
        # Verify pattern recording
        pattern_id = "SELECT_time > 2023-01-01"
        self.assertIn(pattern_id, self.adaptive.query_patterns)
        pattern = self.adaptive.query_patterns[pattern_id]
        self.assertEqual(pattern.frequency, 2)
        self.assertAlmostEqual(pattern.avg_execution_time, 1.25)
        
    def test_pattern_cleanup(self):
        """Test cleanup of old query patterns."""
        # Add old pattern
        old_time = datetime.now() - timedelta(days=10)
        self.adaptive.query_patterns["old_pattern"] = QueryPattern(
            pattern_id="old_pattern",
            query_type="SELECT",
            predicates=["old"],
            frequency=1,
            avg_execution_time=1.0,
            last_seen=old_time,
            affected_indexes=set()
        )
        
        # Add current pattern
        self.adaptive.analyze_query_pattern(
            query_type="SELECT",
            predicates=["current"],
            execution_time=1.0,
            affected_indexes={"index_0"}
        )
        
        # Trigger cleanup
        self.adaptive._cleanup_patterns()
        
        # Verify old pattern removed
        self.assertNotIn("old_pattern", self.adaptive.query_patterns)
        
    def test_index_scoring(self):
        """Test index scoring system."""
        # Add query patterns
        self.adaptive.analyze_query_pattern(
            query_type="SELECT",
            predicates=["time > 2023-01-01"],
            execution_time=1.0,
            affected_indexes={"index_0"}
        )
        
        # Verify scores calculated
        self.assertIn("index_0", self.adaptive.index_scores)
        self.assertGreater(self.adaptive.index_scores["index_0"], 0)
        
        # Verify score components
        query_score = self.adaptive._calculate_query_score("index_0")
        self.assertEqual(query_score, 1.0)  # Only index used
        
        size_score = self.adaptive._calculate_size_score(102400)
        self.assertGreater(size_score, 0)
        
    def test_partitioning_recommendations(self):
        """Test partitioning strategy recommendations."""
        # Add time-based query patterns
        self.adaptive.analyze_query_pattern(
            query_type="SELECT",
            predicates=["time > 2023-01-01", "time < 2023-12-31"],
            execution_time=1.0,
            affected_indexes={"index_0"}
        )
        
        # Get recommendations
        rec = self.adaptive.recommend_partitioning("index_0")
        self.assertIsNotNone(rec)
        
        strategy, boundaries = rec
        self.assertEqual(strategy, PartitionStrategy.TIME_SERIES)
        self.assertGreater(len(boundaries), 0)
        
    def test_maintenance_scheduling(self):
        """Test maintenance scheduling."""
        # Schedule maintenance
        self.adaptive.schedule_maintenance(
            "index_0",
            "REINDEX",
            priority=1
        )
        
        # Get next maintenance
        next_maintenance = self.adaptive.get_next_maintenance()
        self.assertIsNotNone(next_maintenance)
        
        timestamp, index_id, operation = next_maintenance
        self.assertEqual(index_id, "index_0")
        self.assertEqual(operation, "REINDEX")
        
        # Verify scheduled in maintenance window
        window = self.adaptive.config["maintenance_window"]
        self.assertTrue(
            window["start_hour"] <= timestamp.hour <= window["end_hour"]
        )
        
    def test_index_recommendations(self):
        """Test index recommendations."""
        # Add patterns and update scores
        self.adaptive.analyze_query_pattern(
            query_type="SELECT",
            predicates=["time > 2023-01-01"],
            execution_time=1.0,
            affected_indexes={"index_0"}
        )
        
        # Get recommendations
        recommendations = self.adaptive.get_index_recommendations(
            min_score=0.0  # Include all for testing
        )
        
        self.assertGreater(len(recommendations), 0)
        for index_id, score, details in recommendations:
            self.assertIsInstance(score, float)
            self.assertIn("current_size", details)
            self.assertIn("fragmentation", details)
            self.assertIn("recommended_partitioning", details)
            
    def test_adaptive_behavior(self):
        """Test adaptive behavior over time."""
        # Simulate query patterns over time
        for i in range(10):
            self.adaptive.analyze_query_pattern(
                query_type="SELECT",
                predicates=[f"field_{i} > value"],
                execution_time=1.0 + (i * 0.1),
                affected_indexes={f"index_{i % 5}"}
            )
            time.sleep(0.1)  # Small delay
            
        # Verify pattern evolution
        self.assertGreater(len(self.adaptive.query_patterns), 0)
        
        # Verify score updates
        scores_before = self.adaptive.index_scores.copy()
        
        # Add new patterns
        self.adaptive.analyze_query_pattern(
            query_type="SELECT",
            predicates=["new_field > value"],
            execution_time=1.0,
            affected_indexes={"index_0"}
        )
        
        # Verify scores updated
        self.assertNotEqual(
            scores_before["index_0"],
            self.adaptive.index_scores["index_0"]
        )
        
    def test_configuration_handling(self):
        """Test configuration handling."""
        # Test default config
        adaptive_default = AdaptiveIndexManager(
            self.store,
            self.manager,
            self.optimizer
        )
        self.assertIsNotNone(adaptive_default.config)
        
        # Test custom config
        custom_config = {
            "partition_size_threshold": 2048 * 1024,
            "max_partitions_per_index": 20
        }
        
        config_path = Path(self.temp_dir) / "custom_config.json"
        with open(config_path, 'w') as f:
            json.dump(custom_config, f)
            
        adaptive_custom = AdaptiveIndexManager(
            self.store,
            self.manager,
            self.optimizer,
            config_path
        )
        
        self.assertEqual(
            adaptive_custom.config["partition_size_threshold"],
            2048 * 1024
        ) 