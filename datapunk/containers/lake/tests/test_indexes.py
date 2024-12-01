import unittest
from typing import List
from ..src.storage.index.hash import HashIndex
from ..src.storage.index.bitmap import BitmapIndex, CompressionType
from ..src.storage.index.core import IndexType

class TestHashIndex(unittest.TestCase):
    def setUp(self):
        self.index = HashIndex("test_hash", "test_table", ["col1"])
        
    def test_insert_and_search(self):
        self.index.insert("key1", 1)
        self.index.insert("key1", 2)
        self.index.insert("key2", 3)
        
        self.assertEqual(self.index.search("key1"), [1, 2])
        self.assertEqual(self.index.search("key2"), [3])
        self.assertEqual(self.index.search("key3"), [])
        
    def test_delete(self):
        self.index.insert("key1", 1)
        self.index.insert("key1", 2)
        self.index.delete("key1", 1)
        
        self.assertEqual(self.index.search("key1"), [2])
        
    def test_rebuild(self):
        self.index.insert("key1", 1)
        self.index.insert("key2", 2)
        self.index.delete("key1", 1)
        
        initial_stats = self.index.get_statistics()
        self.index.rebuild()
        final_stats = self.index.get_statistics()
        
        self.assertEqual(self.index.search("key2"), [2])
        self.assertLess(final_stats["total_entries"], initial_stats["total_entries"])
        
    def test_collision_handling(self):
        # Create keys that might have hash collisions
        key1 = "abc"
        key2 = "cba"  # Different key that might hash to same value
        
        self.index.insert(key1, 1)
        self.index.insert(key2, 2)
        
        self.assertEqual(self.index.search(key1), [1])
        self.assertEqual(self.index.search(key2), [2])
        
class TestBitmapIndex(unittest.TestCase):
    def setUp(self):
        self.uncompressed_index = BitmapIndex("test_bitmap", "test_table", ["col1"])
        self.wah_index = BitmapIndex("test_wah", "test_table", ["col1"], 
                                   compression_type=CompressionType.WAH)
        self.concise_index = BitmapIndex("test_concise", "test_table", ["col1"],
                                       compression_type=CompressionType.CONCISE)
        self.roaring_index = BitmapIndex("test_roaring", "test_table", ["col1"],
                                       compression_type=CompressionType.ROARING)
        self.indexes = [
            self.uncompressed_index,
            self.wah_index,
            self.concise_index,
            self.roaring_index
        ]
        
    def test_insert_and_search(self):
        for index in self.indexes:
            with self.subTest(compression=index._compression_type):
                index.insert(1, 0)
                index.insert(1, 2)
                index.insert(2, 1)
                
                self.assertEqual(index.search(1), [0, 2])
                self.assertEqual(index.search(2), [1])
        
    def test_range_search(self):
        for index in self.indexes:
            with self.subTest(compression=index._compression_type):
                for i in range(5):
                    index.insert(i, i)
                    
                range_result = index.range_search(1, 3)
                self.assertEqual(set(range_result), {1, 2, 3})
        
    def test_delete_and_rebuild(self):
        for index in self.indexes:
            with self.subTest(compression=index._compression_type):
                for i in range(5):
                    index.insert(i, i)
                    
                index.delete(2, 2)
                index.delete(3, 3)
                
                initial_stats = index.get_statistics()
                index.rebuild()
                final_stats = index.get_statistics()
                
                self.assertLess(final_stats["total_rows"], initial_stats["total_rows"])
                self.assertEqual(final_stats["deleted_rows"], 0)
        
    def test_bitmap_extension(self):
        for index in self.indexes:
            with self.subTest(compression=index._compression_type):
                index.insert(1, 0)
                index.insert(1, 10)  # Should cause extension
                
                self.assertEqual(index.search(1), [0, 10])
                self.assertGreaterEqual(index._row_count, 11)
        
    def test_statistics(self):
        for index in self.indexes:
            with self.subTest(compression=index._compression_type):
                for i in range(3):
                    index.insert(1, i)
                for i in range(3, 5):
                    index.insert(2, i)
                    
                stats = index.get_statistics()
                self.assertEqual(stats["distinct_values"], 2)
                self.assertEqual(stats["total_bits_set"], 5)
                self.assertEqual(stats["total_rows"], 5)
                
                if index._compressor:
                    self.assertIn("compression_ratio", stats)
                    self.assertIn("compressed_size_bytes", stats)
                    self.assertIn("uncompressed_size_bytes", stats)
                    self.assertGreater(stats["uncompressed_size_bytes"], 0)
                    
    def test_compression_efficiency(self):
        """Test compression efficiency with different patterns."""
        for index in self.indexes:
            if not index._compressor:
                continue
                
            with self.subTest(compression=index._compression_type):
                # Create repeating pattern (good for WAH/CONCISE)
                for i in range(100):
                    index.insert(1, i * 2)  # Every even position
                    
                # Create sparse data (good for Roaring)
                for i in range(1000):
                    if i % 100 == 0:
                        index.insert(2, i)
                        
                stats = index.get_statistics()
                self.assertLess(stats["compression_ratio"], 1.0,
                              "Compressed size should be smaller than uncompressed")
                
if __name__ == '__main__':
    unittest.main() 