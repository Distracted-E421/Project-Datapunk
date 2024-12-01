import unittest
from typing import List, Set
import re
import threading
import random

from ..src.storage.index.strategies.regex import (
    RegexPattern,
    RegexStrategy,
    create_regex_index
)

class TestRegexPattern(unittest.TestCase):
    def test_pattern_creation(self):
        # Test basic pattern
        pattern = RegexPattern.from_regex("hello.*world")
        self.assertEqual(pattern.prefix, "hello")
        self.assertEqual(pattern.suffix, "world")
        self.assertEqual(pattern.literals, {"hello", "world"})
        self.assertEqual(pattern.min_length, 10)  # "hello" + "world"
        
        # Test pattern with quantifiers
        pattern = RegexPattern.from_regex("ab{2,4}c")
        self.assertEqual(pattern.prefix, "ab")
        self.assertEqual(pattern.suffix, "c")
        self.assertEqual(pattern.min_length, 4)  # "a" + "bb" + "c"
        self.assertEqual(pattern.max_length, 6)  # "a" + "bbbb" + "c"
        
        # Test pattern with alternation
        pattern = RegexPattern.from_regex("(foo|bar)baz")
        self.assertEqual(pattern.suffix, "baz")
        self.assertTrue("baz" in pattern.literals)
        
    def test_pattern_matching(self):
        pattern = RegexPattern.from_regex("hello.*world")
        
        # Test direct matches
        self.assertTrue(pattern.matches("hello world"))
        self.assertTrue(pattern.matches("hello beautiful world"))
        self.assertFalse(pattern.matches("hi world"))
        self.assertFalse(pattern.matches("hello earth"))
        
        # Test case sensitivity
        pattern_i = RegexPattern.from_regex("hello.*world", is_case_sensitive=False)
        self.assertTrue(pattern_i.matches("HELLO WORLD"))
        self.assertTrue(pattern_i.matches("Hello World"))
        
    def test_pattern_compression(self):
        # Create a complex pattern
        text = "".join(chr(i) for i in range(97, 123))  # a-z
        pattern = RegexPattern.from_regex(text + ".*")
        
        # Test compression
        compressed = pattern.compress(max_trigrams=5)
        self.assertTrue(len(compressed.pattern) < len(pattern.pattern))
        self.assertTrue(compressed.compressed)
        
    def test_pattern_intersection(self):
        pattern1 = RegexPattern.from_regex("hello.*")
        pattern2 = RegexPattern.from_regex(".*world")
        
        # Patterns that could match the same strings
        self.assertTrue(pattern1.could_match(pattern2))
        
        # Patterns that cannot match the same strings
        pattern3 = RegexPattern.from_regex("^[0-9]+$")
        self.assertFalse(pattern1.could_match(pattern3))

class TestRegexStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = RegexStrategy(compression_threshold=50)
        
    def test_consistency(self):
        entry = RegexPattern.from_regex("hello.*world")
        
        # Test string queries
        self.assertTrue(self.strategy.consistent(entry, "hello world"))
        self.assertTrue(self.strategy.consistent(entry, "hello beautiful world"))
        self.assertFalse(self.strategy.consistent(entry, "hi world"))
        
        # Test pattern queries
        query = RegexPattern.from_regex("hello.*")
        self.assertTrue(self.strategy.consistent(entry, query))
        
        query = RegexPattern.from_regex("[0-9]+")
        self.assertFalse(self.strategy.consistent(entry, query))
        
    def test_union(self):
        patterns = [
            RegexPattern.from_regex("hello.*"),
            RegexPattern.from_regex("hi.*"),
            RegexPattern.from_regex("hey.*")
        ]
        
        union = self.strategy.union(patterns)
        
        # Union should match any of the original patterns
        self.assertTrue(union.matches("hello world"))
        self.assertTrue(union.matches("hi there"))
        self.assertTrue(union.matches("hey you"))
        
        # Common properties should be preserved
        self.assertEqual(union.min_length, min(p.min_length for p in patterns))
        
    def test_compression(self):
        # Create a complex pattern
        pattern = RegexPattern.from_regex("(this|that|those).*is.*(test|example|sample)")
        
        compressed = self.strategy.compress(pattern)
        
        # Compressed pattern should be simpler but maintain key constraints
        self.assertTrue(len(compressed.pattern) < len(pattern.pattern))
        self.assertTrue(compressed.matches("this is a test"))
        self.assertTrue(compressed.matches("that is an example"))
        
    def test_penalty(self):
        pattern1 = RegexPattern.from_regex("hello.*world")
        pattern2 = RegexPattern.from_regex("hello.*earth")
        pattern3 = RegexPattern.from_regex("[0-9]+")
        
        # Similar patterns should have lower penalty
        penalty12 = self.strategy.penalty(pattern1, pattern2)
        penalty13 = self.strategy.penalty(pattern1, pattern3)
        self.assertTrue(penalty12 < penalty13)
        
    def test_pick_split(self):
        patterns = [
            RegexPattern.from_regex("hello.*"),
            RegexPattern.from_regex("hi.*"),
            RegexPattern.from_regex("hey.*"),
            RegexPattern.from_regex("[0-9]+"),
            RegexPattern.from_regex("[a-z]+")
        ]
        
        group1, group2 = self.strategy.pick_split(patterns)
        
        # Both groups should be non-empty
        self.assertTrue(len(group1) >= 2)
        self.assertTrue(len(group2) >= 2)
        
        # Total number of patterns should be preserved
        self.assertEqual(len(group1) + len(group2), len(patterns))

class TestRegexIndex(unittest.TestCase):
    def setUp(self):
        self.index = create_regex_index(
            name="test_regex_index",
            table_name="test_table",
            column="text_column"
        )
        
        # Add some test data
        self.test_data = [
            ("hello world", 1),
            ("hello there", 2),
            ("hi everyone", 3),
            ("12345", 4),
            ("test@example.com", 5)
        ]
        
        for text, value in self.test_data:
            self.index.insert(RegexPattern.from_regex(re.escape(text)), value)
            
    def test_exact_search(self):
        # Search for exact matches
        results = self.index.search("hello world")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 1)
        
    def test_pattern_search(self):
        # Search using patterns
        results = self.index.search(RegexPattern.from_regex("hello.*"))
        self.assertEqual(len(results), 2)
        self.assertTrue(all(id in [1, 2] for id in results))
        
        # Search for numbers
        results = self.index.search(RegexPattern.from_regex("^[0-9]+$"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], 4)
        
    def test_large_dataset(self):
        # Create patterns for testing
        patterns = [
            "user[0-9]+",
            "test[a-z]*",
            "data_[0-9]+",
            "[a-z]+@[a-z]+\\.[a-z]{2,3}",
            "ID:[A-Z0-9]+"
        ]
        
        large_index = create_regex_index(
            name="large_regex_index",
            table_name="test_table",
            column="text_column"
        )
        
        # Insert 1000 random items
        test_data = []
        for i in range(1000):
            pattern = random.choice(patterns)
            # Generate a string matching the pattern
            if pattern == "user[0-9]+":
                text = f"user{random.randint(1, 999)}"
            elif pattern == "test[a-z]*":
                text = "test" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=random.randint(0, 5)))
            elif pattern == "data_[0-9]+":
                text = f"data_{random.randint(1, 999)}"
            elif pattern == "[a-z]+@[a-z]+\\.[a-z]{2,3}":
                text = f"user{i}@example.com"
            else:  # ID:[A-Z0-9]+
                text = f"ID:" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=6))
                
            test_data.append((text, i))
            large_index.insert(RegexPattern.from_regex(re.escape(text)), i)
            
        # Test various search patterns
        results = large_index.search(RegexPattern.from_regex("user[0-9]+"))
        self.assertTrue(len(results) > 0)
        
        results = large_index.search(RegexPattern.from_regex(".*@example\\.com"))
        self.assertTrue(len(results) > 0)
        
        # Verify results
        for result in results:
            text = next(text for text, i in test_data if i == result)
            self.assertTrue("@example.com" in text)
            
    def test_concurrent_operations(self):
        def insert_random_patterns(thread_id: int, count: int):
            patterns = [
                f"thread{thread_id}_[0-9]+",
                f"test{thread_id}_[a-z]+",
                f"data{thread_id}_.*"
            ]
            
            for i in range(count):
                pattern = random.choice(patterns)
                text = f"thread{thread_id}_test_{i}"
                self.index.insert(RegexPattern.from_regex(pattern), f"T{thread_id}_{i}")
                
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=insert_random_patterns,
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
        results = self.index.search(RegexPattern.from_regex("thread[0-9]+_.*"))
        self.assertEqual(len(results), 300)  # All thread-created entries 