import unittest
from typing import List, Tuple, Any
import numpy as np
import threading
import random

from ..src.storage.index.gist import GiSTIndex, GiSTPredicateStrategy
from ..src.storage.index.strategies.trigram import (
    TrigramSet,
    TrigramStrategy,
    create_trigram_index
)

class TestTrigramSet(unittest.TestCase):
    def test_creation(self):
        text = "hello"
        trigram_set = TrigramSet.from_text(text)
        expected_trigrams = {"  h", " he", "hel", "ell", "llo", "lo ", "o  "}
        self.assertEqual(trigram_set.trigrams, expected_trigrams)
        
    def test_similarity(self):
        set1 = TrigramSet.from_text("hello")
        set2 = TrigramSet.from_text("help")
        
        similarity = set1.similarity(set2)
        self.assertTrue(0 < similarity < 1)  # Should be partially similar
        
        # Same text should have similarity 1
        self.assertEqual(set1.similarity(TrigramSet.from_text("hello")), 1.0)
        
        # Completely different texts should have similarity 0
        set3 = TrigramSet.from_text("xyz")
        self.assertEqual(set1.similarity(set3), 0.0)
        
    def test_contains(self):
        set1 = TrigramSet.from_text("hello world")
        set2 = TrigramSet.from_text("hello")
        
        self.assertTrue(set1.contains(set2))
        self.assertFalse(set2.contains(set1))
        
    def test_compression(self):
        # Create a large text to generate many trigrams
        text = "".join(chr(i) for i in range(97, 123)) * 3  # a-z repeated 3 times
        trigram_set = TrigramSet.from_text(text)
        
        compressed = trigram_set.compress(max_trigrams=10)
        self.assertTrue(compressed.compressed)
        self.assertEqual(len(compressed.trigrams), 10)

class TestTrigramStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = TrigramStrategy(similarity_threshold=0.3)
        
    def test_consistent(self):
        entry = TrigramSet.from_text("hello world")
        
        # Test with string query
        self.assertTrue(self.strategy.consistent(entry, "hello"))
        self.assertFalse(self.strategy.consistent(entry, "xyz"))
        
        # Test with TrigramSet query
        query = TrigramSet.from_text("hello")
        self.assertTrue(self.strategy.consistent(entry, query))
        
        # Test with invalid query type
        self.assertFalse(self.strategy.consistent(entry, 123))
        
    def test_union(self):
        entries = [
            TrigramSet.from_text("hello"),
            TrigramSet.from_text("world")
        ]
        
        union = self.strategy.union(entries)
        
        # Union should contain trigrams from both entries
        for entry in entries:
            self.assertTrue(union.contains(entry))
            
    def test_compression(self):
        entry = TrigramSet.from_text("hello world")
        compressed = self.strategy.compress(entry)
        
        # Compression should maintain some similarity
        self.assertTrue(compressed.similarity(entry) > 0.5)
        
    def test_penalty(self):
        entry1 = TrigramSet.from_text("hello")
        entry2 = TrigramSet.from_text("help")
        
        penalty = self.strategy.penalty(entry1, entry2)
        self.assertTrue(isinstance(penalty, (int, float)))
        self.assertTrue(penalty >= 0)
        
    def test_pick_split(self):
        entries = [
            TrigramSet.from_text("hello"),
            TrigramSet.from_text("world"),
            TrigramSet.from_text("help"),
            TrigramSet.from_text("heap"),
            TrigramSet.from_text("xyz")
        ]
        
        group1, group2 = self.strategy.pick_split(entries)
        
        # Both groups should be non-empty
        self.assertTrue(len(group1) >= 2)
        self.assertTrue(len(group2) >= 2)
        
        # Total number of entries should be preserved
        self.assertEqual(len(group1) + len(group2), len(entries))

class TestGiSTIndex(unittest.TestCase):
    def setUp(self):
        self.index = create_trigram_index(
            name="test_trigram_index",
            table_name="test_table",
            column="text_column"
        )
        
        # Add some test data
        self.test_data = [
            ("hello world", 1),
            ("hello there", 2),
            ("world peace", 3),
            ("peaceful day", 4),
            ("xyz abc", 5)
        ]
        
        for text, value in self.test_data:
            self.index.insert(TrigramSet.from_text(text), value)
            
    def test_search(self):
        # Search for entries containing "hello"
        results = self.index.search("hello")
        self.assertEqual(len(results), 2)
        self.assertTrue(all(id in [1, 2] for id in results))
        
        # Search for entries containing "peace"
        results = self.index.search("peace")
        self.assertEqual(len(results), 2)
        self.assertTrue(all(id in [3, 4] for id in results))
        
        # Search for non-existent text
        results = self.index.search("nonexistent")
        self.assertEqual(len(results), 0)
        
    def test_large_dataset(self):
        # Create a larger dataset for performance testing
        words = ["hello", "world", "peace", "love", "joy", "happy", "sad", "blue", "red", "green"]
        large_index = create_trigram_index(
            name="large_trigram_index",
            table_name="test_table",
            column="text_column"
        )
        
        # Insert 1000 random combinations of words
        for i in range(1000):
            text = " ".join(random.choices(words, k=3))
            large_index.insert(TrigramSet.from_text(text), i)
            
        # Test search performance
        results = large_index.search("hello world")
        self.assertTrue(len(results) > 0)
        
        # Get statistics
        stats = large_index.get_statistics()
        self.assertEqual(stats.total_entries, 1000)
        self.assertTrue(stats.avg_lookup_time_ms > 0)
        
    def test_concurrent_operations(self):
        def insert_random_texts(thread_id: int, count: int):
            words = ["thread", "test", "concurrent", "operation", "index"]
            for i in range(count):
                text = f"thread{thread_id} " + " ".join(random.choices(words, k=2))
                self.index.insert(TrigramSet.from_text(text), f"T{thread_id}_{i}")
                
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=insert_random_texts,
                args=(i, 100)
            )
            threads.append(thread)
            
        # Start all threads
        for thread in threads:
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        # Verify the index is still consistent
        stats = self.index.get_statistics()
        self.assertEqual(stats.total_entries, 305)  # 5 original + 300 new
        
        # Test search still works
        results = self.index.search("thread")
        self.assertEqual(len(results), 300)  # All thread-created entries
        
    def test_cleanup(self):
        # Add some data and verify it exists
        self.assertTrue(self.index.size > 0)
        
        # Cleanup
        self.index.cleanup()
        
        # Verify everything is cleaned up
        self.assertEqual(self.index.size, 0)
        self.assertIsNone(self.index.root)
        self.assertEqual(len(self.index._insert_times), 0)
        self.assertEqual(len(self.index._search_times), 0) 