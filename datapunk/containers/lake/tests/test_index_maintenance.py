import unittest
from datetime import datetime, timedelta
from typing import List
from ..src.storage.index.core import Index, IndexType
from ..src.storage.index.advisor import IndexAdvisor
from ..src.storage.index.maintenance import IndexMaintenanceManager, IndexUsageStats
from ..src.storage.index.composite import CompositeIndex
from ..src.query.optimizer.index_aware import IndexAwareOptimizer, IndexAccessPath
from ..src.query.parser.core import QueryNode, QueryType

class MockIndex(Index):
    """Mock index for testing."""
    def __init__(self, name: str, table_name: str, column_names: List[str]):
        super().__init__(name, table_name, column_names, IndexType.BTREE)
        self.rebuild_called = False
        
    def rebuild(self) -> None:
        self.rebuild_called = True

class TestIndexMaintenance(unittest.TestCase):
    def setUp(self):
        self.advisor = IndexAdvisor()
        self.manager = IndexMaintenanceManager(self.advisor)
        self.index = MockIndex("test_index", "test_table", ["col1"])
        self.manager.register_index(self.index)
        
    def test_usage_tracking(self):
        # Record various operations
        self.manager.record_operation("test_index", "lookup", 10.0)
        self.manager.record_operation("test_index", "update", 5.0)
        self.manager.record_operation("test_index", "range_scan")
        
        # Verify statistics
        stats = self.manager.get_index_statistics()["test_index"]
        self.assertEqual(stats["total_lookups"], 1)
        self.assertEqual(stats["total_updates"], 1)
        self.assertEqual(stats["total_range_scans"], 1)
        self.assertEqual(stats["avg_lookup_time_ms"], 10.0)
        self.assertEqual(stats["avg_update_time_ms"], 5.0)
        
    def test_maintenance_recommendations(self):
        # Set up conditions that should trigger recommendations
        stats = self.manager.usage_stats["test_index"]
        stats.fragmentation = 35.0  # Above rebuild threshold
        stats.last_used = datetime.now() - timedelta(days=40)  # Unused
        stats.lookup_time_ms = 1000  # Slow lookups
        stats.total_lookups = 10
        
        recommendations = self.manager.analyze_maintenance_needs()
        table_recs = recommendations["test_table"]
        
        self.assertTrue(any("Rebuild" in rec for rec in table_recs))
        self.assertTrue(any("unused" in rec for rec in table_recs))
        self.assertTrue(any("slow" in rec for rec in table_recs))
        
    def test_perform_maintenance(self):
        # Update fragmentation to trigger rebuild
        self.manager.update_statistics("test_index", 1000, 35.0)
        
        # Perform maintenance
        self.manager.perform_maintenance("test_index")
        
        # Verify rebuild was called
        self.assertTrue(self.index.rebuild_called)
        
        # Verify statistics were updated
        stats = self.manager.get_index_statistics()["test_index"]
        self.assertEqual(stats["fragmentation"], 0.0)
        
class TestIndexAwareOptimizer(unittest.TestCase):
    def setUp(self):
        self.advisor = IndexAdvisor()
        self.manager = IndexMaintenanceManager(self.advisor)
        self.optimizer = IndexAwareOptimizer(self.manager)
        
        # Create test indexes
        self.btree_index = CompositeIndex(
            "idx_btree", "users", ["id", "name"], IndexType.BTREE)
        self.hash_index = CompositeIndex(
            "idx_hash", "users", ["email"], IndexType.HASH)
            
        # Register indexes
        self.manager.register_index(self.btree_index)
        self.manager.register_index(self.hash_index)
        self.optimizer.register_table_indexes("users", [self.btree_index, self.hash_index])
        
    def test_access_path_selection(self):
        # Create a test query
        query = QueryNode(
            query_type=QueryType.SELECT,
            tables=["users"],
            conditions=[{"column": "id", "op": "=", "value": 1}],
            order_by=["name"]
        )
        
        # Optimize query
        optimized = self.optimizer.optimize_query(query)
        
        # Verify index usage was recorded
        stats = self.manager.get_index_statistics()
        self.assertIn("idx_btree", stats)
        
    def test_cost_based_selection(self):
        # Set up different performance characteristics
        self.manager.record_operation("idx_btree", "lookup", 5.0)
        self.manager.record_operation("idx_hash", "lookup", 2.0)
        
        # Create a query that could use either index
        query = QueryNode(
            query_type=QueryType.SELECT,
            tables=["users"],
            conditions=[{"column": "id", "op": "=", "value": 1}]
        )
        
        # Optimize query
        optimized = self.optimizer.optimize_query(query)
        
        # Hash index should be preferred for equality search
        stats = self.manager.get_index_statistics()
        self.assertGreater(
            stats["idx_hash"]["total_lookups"],
            stats["idx_btree"]["total_lookups"]
        )
        
    def test_range_scan_handling(self):
        # Create a range query
        query = QueryNode(
            query_type=QueryType.SELECT,
            tables=["users"],
            conditions=[{"column": "id", "op": "BETWEEN", "value": (1, 10)}]
        )
        
        # Optimize query
        optimized = self.optimizer.optimize_query(query)
        
        # Verify B-tree index was chosen for range scan
        stats = self.manager.get_index_statistics()
        self.assertGreater(stats["idx_btree"]["total_range_scans"], 0)
        
    def test_ordering_consideration(self):
        # Create queries with different ordering requirements
        query1 = QueryNode(
            query_type=QueryType.SELECT,
            tables=["users"],
            conditions=[],
            order_by=["name"]
        )
        
        query2 = QueryNode(
            query_type=QueryType.SELECT,
            tables=["users"],
            conditions=[],
            order_by=["email"]
        )
        
        # Optimize queries
        self.optimizer.optimize_query(query1)  # Should use btree_index
        self.optimizer.optimize_query(query2)  # Should use hash_index
        
        # Verify appropriate index selection
        stats = self.manager.get_index_statistics()
        self.assertGreater(stats["idx_btree"]["total_lookups"], 0)
        self.assertGreater(stats["idx_hash"]["total_lookups"], 0)
        
if __name__ == '__main__':
    unittest.main() 