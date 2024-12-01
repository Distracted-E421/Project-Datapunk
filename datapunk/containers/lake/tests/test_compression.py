import unittest
import tempfile
import os
import json
import shutil
from pathlib import Path
import random

from ..src.storage.index.compression import (
    CompressionOptimizer,
    CompressionAlgorithm,
    CompressionLevel
)

class TestCompressionOptimizer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.optimizer = CompressionOptimizer()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def _create_test_file(self, content: str, filename: str = "test.txt") -> Path:
        """Create a test file with given content."""
        file_path = Path(self.temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
        
    def _create_random_binary(self, size: int) -> bytes:
        """Create random binary data."""
        return bytes(random.randint(0, 255) for _ in range(size))
        
    def test_compression_basic(self):
        """Test basic compression functionality."""
        # Create test file
        content = "test " * 1000  # Repeating content for good compression
        input_path = self._create_test_file(content)
        
        # Test compression
        result = self.optimizer.compress_file(input_path)
        
        # Verify compression worked
        self.assertTrue(os.path.exists(result["output_path"]))
        self.assertGreater(result["compression_ratio"], 1.0)
        self.assertEqual(result["algorithm"], CompressionAlgorithm.ZSTD.value)
        
    def test_compression_algorithms(self):
        """Test all compression algorithms."""
        content = "test " * 1000
        input_path = self._create_test_file(content)
        
        for algorithm in CompressionAlgorithm:
            if algorithm != CompressionAlgorithm.NONE:
                optimizer = CompressionOptimizer(
                    algorithm=algorithm,
                    auto_select=False
                )
                
                result = optimizer.compress_file(input_path)
                self.assertEqual(result["algorithm"], algorithm.value)
                
                # Test decompression
                output_path = Path(self.temp_dir) / "decompressed.txt"
                optimizer.decompress_file(
                    result["output_path"],
                    output_path
                )
                
                with open(output_path, 'r', encoding='utf-8') as f:
                    decompressed = f.read()
                self.assertEqual(decompressed, content)
                
    def test_compression_levels(self):
        """Test different compression levels."""
        content = "test " * 1000
        input_path = self._create_test_file(content)
        
        results = {}
        for level in CompressionLevel:
            optimizer = CompressionOptimizer(
                algorithm=CompressionAlgorithm.ZSTD,
                level=level,
                auto_select=False
            )
            
            result = optimizer.compress_file(input_path)
            results[level] = result["output_size"]
            
        # MAX should give smallest file size
        self.assertLess(
            results[CompressionLevel.MAX],
            results[CompressionLevel.FAST]
        )
        
    def test_auto_selection(self):
        """Test automatic algorithm selection."""
        # Test with JSON data
        json_data = {"key": "value" * 100}
        json_path = self._create_test_file(
            json.dumps(json_data),
            "test.json"
        )
        
        result = self.optimizer.compress_file(json_path)
        self.assertEqual(result["algorithm"], CompressionAlgorithm.ZSTD.value)
        
        # Test with high entropy data
        binary_path = Path(self.temp_dir) / "test.bin"
        with open(binary_path, 'wb') as f:
            f.write(self._create_random_binary(1024))
            
        result = self.optimizer.compress_file(binary_path)
        self.assertEqual(result["algorithm"], CompressionAlgorithm.NONE.value)
        
        # Test with small file
        small_path = self._create_test_file("small content", "small.txt")
        result = self.optimizer.compress_file(small_path)
        self.assertEqual(result["algorithm"], CompressionAlgorithm.SNAPPY.value)
        
    def test_compression_metadata(self):
        """Test metadata handling."""
        input_path = self._create_test_file("test content")
        metadata = {
            "description": "Test file",
            "version": "1.0"
        }
        
        result = self.optimizer.compress_file(
            input_path,
            metadata=metadata
        )
        
        self.assertEqual(result["description"], metadata["description"])
        self.assertEqual(result["version"], metadata["version"])
        
    def test_error_handling(self):
        """Test error handling."""
        # Test with non-existent file
        with self.assertRaises(Exception):
            self.optimizer.compress_file("nonexistent.txt")
            
        # Test with invalid compression algorithm
        with self.assertRaises(ValueError):
            self.optimizer.decompress_file(
                self._create_test_file("test"),
                Path(self.temp_dir) / "output.txt"
            )
            
    def test_large_file_handling(self):
        """Test handling of larger files."""
        # Create a 5MB file
        large_content = "x" * (5 * 1024 * 1024)
        large_path = self._create_test_file(large_content, "large.txt")
        
        result = self.optimizer.compress_file(large_path)
        
        # Verify compression completed
        self.assertTrue(os.path.exists(result["output_path"]))
        self.assertGreater(result["compression_ratio"], 1.0)
        
        # Test decompression
        output_path = Path(self.temp_dir) / "decompressed_large.txt"
        self.optimizer.decompress_file(
            result["output_path"],
            output_path
        )
        
        with open(output_path, 'r', encoding='utf-8') as f:
            decompressed = f.read()
        self.assertEqual(len(decompressed), len(large_content))
        
    def test_entropy_calculation(self):
        """Test entropy calculation."""
        # Low entropy (repeating pattern)
        low_entropy = "a" * 1000
        low_path = self._create_test_file(low_entropy)
        
        # High entropy (random data)
        high_entropy = "".join(
            chr(random.randint(0, 255))
            for _ in range(1000)
        )
        high_path = self._create_test_file(high_entropy)
        
        # Verify algorithm selection
        low_result = self.optimizer.compress_file(low_path)
        high_result = self.optimizer.compress_file(high_path)
        
        self.assertNotEqual(
            low_result["algorithm"],
            high_result["algorithm"]
        ) 