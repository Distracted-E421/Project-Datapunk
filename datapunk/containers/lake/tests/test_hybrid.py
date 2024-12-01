import unittest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime, timedelta
import pickle

from ..src.storage.index.hybrid import (
    HashIndex,
    HashConfig,
    HashFunction,
    AutoIndexManager,
    IndexUsagePattern,
    RecoveryPoint
)
from ..src.storage.index.stats import StatisticsStore
from ..src.storage.index.manager import IndexManager
from ..src.storage.index.optimizer import IndexOptimizer

class TestHybridIndexing(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_stats.db"
        self.config_path = Path(self.temp_dir) / "hybrid_config.json"
        
        # Initialize components
        self.store = StatisticsStore(self.db_path)
        self.manager = IndexManager(self.store)
        self.optimizer = IndexOptimizer(self.store)
        
        # Create test configuration
        config = {
            "min_query_frequency": 5,
            "max_candidates": 10,
            "analysis_window_hours": 1,
            "recovery_points_per_index": 3,
            "auto_index_threshold": 0.5,
            "cost_weights": {
                "frequency": 0.4,
                "selectivity": 0.3,
                "maintenance": 0.2,
                "storage": 0.1
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
            
        self.auto_manager = AutoIndexManager(
            self.store,
            self.manager,
            self.optimizer,
            self.config_path
        )
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_hash_index_basic(self):
        """Test basic hash index operations."""
        config = HashConfig(
            function=HashFunction.MURMUR3,
            bucket_count=8,
            max_chain_length=3,
            rehash_threshold=0.75
        )
        
        index = HashIndex(config)
        
        # Test insertion
        self.assertTrue(index.insert("key1", "value1"))
        self.assertTrue(index.insert("key2", "value2"))
        
        # Test retrieval
        self.assertEqual(index.get("key1"), "value1")
        self.assertEqual(index.get("key2"), "value2")
        self.assertIsNone(index.get("nonexistent"))
        
        # Test update
        self.assertTrue(index.insert("key1", "new_value"))
        self.assertEqual(index.get("key1"), "new_value")
        
        # Test deletion
        self.assertTrue(index.delete("key1"))
        self.assertIsNone(index.get("key1"))
        self.assertFalse(index.delete("nonexistent"))
        
    def test_hash_functions(self):
        """Test different hash functions."""
        test_key = "test_key"
        
        for func in HashFunction:
            if func == HashFunction.CUSTOM:
                continue
                
            config = HashConfig(
                function=func,
                bucket_count=16,
                max_chain_length=3,
                rehash_threshold=0.75
            )
            
            index = HashIndex(config)
            hash_val = index._hash_value(test_key)
            
            self.assertIsInstance(hash_val, int)
            self.assertGreaterEqual(hash_val, 0)
            self.assertLess(hash_val, config.bucket_count)
            
    def test_hash_collisions(self):
        """Test hash collision handling."""
        config = HashConfig(
            function=HashFunction.MURMUR3,
            bucket_count=4,  # Small bucket count to force collisions
            max_chain_length=2,
            rehash_threshold=0.75
        )
        
        index = HashIndex(config)
        
        # Insert items to force collisions
        for i in range(10):
            key = f"key_{i}"
            self.assertTrue(index.insert(key, i))
            
        # Verify all items are retrievable
        for i in range(10):
            key = f"key_{i}"
            self.assertEqual(index.get(key), i)
            
        # Verify bucket count increased
        self.assertGreater(index.config.bucket_count, 4)
        
    def test_custom_hash_function(self):
        """Test custom hash function."""
        def custom_hash(key: str) -> int:
            return sum(ord(c) for c in str(key))
            
        config = HashConfig(
            function=HashFunction.CUSTOM,
            bucket_count=16,
            max_chain_length=3,
            rehash_threshold=0.75,
            custom_hash_func=custom_hash
        )
        
        index = HashIndex(config)
        self.assertTrue(index.insert("test", "value"))
        self.assertEqual(index.get("test"), "value")
        
    def test_auto_indexing(self):
        """Test automatic index creation."""
        # Simulate query patterns
        for i in range(10):
            self.auto_manager.analyze_query(
                query_type="SELECT",
                columns=["column1"],
                operators=["="],
                execution_stats={
                    "duration_ms": 100,
                    "selectivity": 0.1,
                    "write_frequency": 0.1
                }
            )
            
        # Verify candidate creation
        self.assertGreater(len(self.auto_manager.candidate_indexes), 0)
        
        # Create recommended indexes
        self.auto_manager.create_recommended_indexes()
        
        # Verify index creation
        pattern_key = "SELECT_column1"
        self.assertIn(pattern_key, self.auto_manager.usage_patterns)
        
    def test_recovery_points(self):
        """Test index recovery points."""
        # Create index
        config = HashConfig(
            function=HashFunction.MURMUR3,
            bucket_count=8,
            max_chain_length=3,
            rehash_threshold=0.75
        )
        
        index = HashIndex(config)
        index.insert("key1", "value1")
        
        # Create recovery point
        self.auto_manager._create_recovery_point(
            "test_index",
            "hash",
            index
        )
        
        # Verify recovery point creation
        self.assertIn("test_index", self.auto_manager.recovery_points)
        points = self.auto_manager.recovery_points["test_index"]
        self.assertEqual(len(points), 1)
        
        # Recover index
        recovered = self.auto_manager.recover_index("test_index")
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered.get("key1"), "value1")
        
    def test_benefit_scoring(self):
        """Test index benefit scoring."""
        # Create test pattern
        pattern = IndexUsagePattern(
            query_type="SELECT",
            column_names=["column1"],
            operators=["="],
            frequency=10,
            avg_selectivity=0.1,
            last_used=datetime.now(),
            execution_stats={
                "duration_ms": 100,
                "write_frequency": 1
            }
        )
        
        # Calculate score
        score = self.auto_manager._calculate_benefit_score(pattern)
        
        # Verify score components
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)
        
    def test_multiple_recovery_points(self):
        """Test multiple recovery points per index."""
        config = HashConfig(
            function=HashFunction.MURMUR3,
            bucket_count=8,
            max_chain_length=3,
            rehash_threshold=0.75
        )
        
        index = HashIndex(config)
        
        # Create multiple versions
        for i in range(5):
            index.insert(f"key_{i}", f"value_{i}")
            self.auto_manager._create_recovery_point(
                "test_index",
                "hash",
                index
            )
            
        # Verify point limit
        points = self.auto_manager.recovery_points["test_index"]
        self.assertLessEqual(
            len(points),
            self.auto_manager.config["recovery_points_per_index"]
        )
        
        # Verify recovery from specific point
        first_point = points[0]
        recovered = self.auto_manager.recover_index(
            "test_index",
            first_point.timestamp
        )
        self.assertIsNotNone(recovered)
        
    def test_error_handling(self):
        """Test error handling."""
        # Test invalid hash function
        with self.assertRaises(ValueError):
            config = HashConfig(
                function=HashFunction.CUSTOM,
                bucket_count=8,
                max_chain_length=3,
                rehash_threshold=0.75
            )
            index = HashIndex(config)
            index._hash_value("test")
            
        # Test recovery with invalid checksum
        config = HashConfig(
            function=HashFunction.MURMUR3,
            bucket_count=8,
            max_chain_length=3,
            rehash_threshold=0.75
        )
        
        index = HashIndex(config)
        self.auto_manager._create_recovery_point(
            "test_index",
            "hash",
            index
        )
        
        # Corrupt recovery point
        point = self.auto_manager.recovery_points["test_index"][0]
        point.checksum = "invalid"
        
        # Attempt recovery
        recovered = self.auto_manager.recover_index("test_index")
        self.assertIsNone(recovered) 