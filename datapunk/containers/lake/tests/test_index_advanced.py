import unittest
from typing import List
from ..src.storage.index.core import IndexType
from ..src.storage.index.composite import CompositeIndex, CompositeKey
from ..src.storage.index.advisor import IndexAdvisor, QueryPattern, ColumnStats

class TestCompositeIndex(unittest.TestCase):
    def setUp(self):
        self.btree_index = CompositeIndex("test_btree", "test_table", 
                                        ["col1", "col2"], IndexType.BTREE)
        self.hash_index = CompositeIndex("test_hash", "test_table",
                                       ["col1", "col2"], IndexType.HASH)
                                       
    def test_insert_and_search(self):
        self.btree_index.insert([1, "a"], 1)
        self.btree_index.insert([1, "b"], 2)
        self.btree_index.insert([2, "a"], 3)
        
        # Test exact match
        self.assertEqual(self.btree_index.search([1, "a"]), [1])
        self.assertEqual(self.btree_index.search([2, "a"]), [3])
        
        # Test prefix match (B-tree only)
        self.assertEqual(set(self.btree_index.search([1])), {1, 2})
        
    def test_hash_index_constraints(self):
        self.hash_index.insert([1, "a"], 1)
        self.hash_index.insert([1, "b"], 2)
        
        # Hash index requires exact match
        self.assertEqual(self.hash_index.search([1, "a"]), [1])
        self.assertEqual(self.hash_index.search([1]), [])  # Prefix not supported
        
    def test_range_search(self):
        for i in range(5):
            self.btree_index.insert([i, chr(97 + i)], i)  # [0,'a'] to [4,'e']
            
        # Test range search on first column
        result = self.btree_index.range_search([1], [3])
        self.assertEqual(set(result), {1, 2, 3})
        
        # Test range search on both columns
        result = self.btree_index.range_search([1, "b"], [3, "d"])
        self.assertEqual(set(result), {1, 2, 3})
        
        # Hash index doesn't support range search
        with self.assertRaises(NotImplementedError):
            self.hash_index.range_search([1], [3])
            
    def test_delete(self):
        self.btree_index.insert([1, "a"], 1)
        self.btree_index.insert([1, "b"], 2)
        self.btree_index.delete([1, "a"], 1)
        
        self.assertEqual(self.btree_index.search([1, "a"]), [])
        self.assertEqual(self.btree_index.search([1, "b"]), [2])
        
    def test_statistics(self):
        for i in range(3):
            self.btree_index.insert([1, chr(97 + i)], i)
            
        stats = self.btree_index.get_statistics()
        self.assertEqual(stats["column_count"], 2)
        self.assertTrue(stats["supports_prefix_search"])
        self.assertTrue(stats["supports_range_search"])
        
class TestIndexAdvisor(unittest.TestCase):
    def setUp(self):
        self.advisor = IndexAdvisor()
        
        # Add some column statistics
        self.advisor.add_column_stats("users", "id", 
                                    ColumnStats(1000, 0, 1000))  # High cardinality
        self.advisor.add_column_stats("users", "status",
                                    ColumnStats(3, 0, 1000))    # Low cardinality
        self.advisor.add_column_stats("users", "age",
                                    ColumnStats(100, 0, 1000))  # Medium cardinality
                                    
    def test_single_column_recommendations(self):
        # Add query patterns
        self.advisor.add_query_pattern(
            QueryPattern("users", ["id"], is_equality=True))
        self.advisor.add_query_pattern(
            QueryPattern("users", ["status"], is_equality=True))
        self.advisor.add_query_pattern(
            QueryPattern("users", ["age"], is_range=True))
            
        recommendations = self.advisor.recommend_indexes("users")
        
        # Verify recommendations
        self.assertEqual(len(recommendations), 3)
        
        # Check specific recommendations
        rec_dict = {cols[0]: type for cols, type in recommendations}
        self.assertEqual(rec_dict["id"], IndexType.HASH)      # High cardinality -> Hash
        self.assertEqual(rec_dict["status"], IndexType.BITMAP)  # Low cardinality -> Bitmap
        self.assertEqual(rec_dict["age"], IndexType.BTREE)    # Range query -> B-tree
        
    def test_composite_index_recommendations(self):
        # Add composite query pattern
        self.advisor.add_query_pattern(
            QueryPattern("users", ["status", "age"], 
                        is_equality=True, frequency=10))
                        
        # Add existing index
        existing_index = CompositeIndex("test_composite", "users",
                                      ["status", "age"], IndexType.BTREE)
        self.advisor.register_existing_index(existing_index)
        
        # Pattern should be covered by existing index
        recommendations = self.advisor.recommend_indexes("users")
        self.assertEqual(len(recommendations), 0)
        
    def test_workload_analysis(self):
        # Add various query patterns
        self.advisor.add_query_pattern(
            QueryPattern("users", ["id"], is_equality=True, frequency=100))
        self.advisor.add_query_pattern(
            QueryPattern("users", ["status", "age"], is_range=True, frequency=50))
            
        analysis = self.advisor.analyze_workload()
        
        self.assertIn("users", analysis)
        recommendations = analysis["users"]
        
        # Verify recommendations are ordered by frequency
        self.assertTrue(any("HASH" in rec for rec in recommendations))
        self.assertTrue(any("BTREE" in rec for rec in recommendations))
        
    def test_compression_recommendations(self):
        # Add a very low cardinality column with many rows
        self.advisor.add_column_stats("logs", "level",
                                    ColumnStats(3, 0, 1000000))
                                    
        self.advisor.add_query_pattern(
            QueryPattern("logs", ["level"], is_equality=True))
            
        analysis = self.advisor.analyze_workload()
        
        # Should recommend bitmap index with compression
        self.assertTrue(any("compression" in rec 
                          for rec in analysis["logs"]))
                          
if __name__ == '__main__':
    unittest.main() 