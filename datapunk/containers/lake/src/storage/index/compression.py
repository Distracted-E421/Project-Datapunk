from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from bitarray import bitarray
from enum import Enum
import gzip
import lzma
import zstd
import snappy
import json
import logging
from typing import Any, Dict, Union, Optional
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class BitmapCompression(ABC):
    """Base class for bitmap compression algorithms."""
    
    @abstractmethod
    def compress(self, bitmap: bitarray) -> bytes:
        """Compress a bitmap into bytes."""
        pass
        
    @abstractmethod
    def decompress(self, data: bytes) -> bitarray:
        """Decompress bytes back into a bitmap."""
        pass

class WAHCompression(BitmapCompression):
    """Word-Aligned Hybrid compression for bitmaps."""
    
    WORD_SIZE = 32
    LITERAL_FLAG = 0x80000000
    
    def compress(self, bitmap: bitarray) -> bytes:
        result = []
        current_pos = 0
        
        while current_pos < len(bitmap):
            # Get current word
            word_end = min(current_pos + self.WORD_SIZE - 1, len(bitmap))
            current_word = bitmap[current_pos:word_end]
            
            # Check if it's a fill word (all 0s or all 1s)
            if all(current_word) or not any(current_word):
                # Count consecutive fill words
                fill_value = current_word[0]
                fill_count = 1
                next_pos = word_end
                
                while next_pos < len(bitmap):
                    next_word = bitmap[next_pos:min(next_pos + self.WORD_SIZE - 1, len(bitmap))]
                    if all(bit == fill_value for bit in next_word):
                        fill_count += 1
                        next_pos += self.WORD_SIZE
                    else:
                        break
                        
                # Encode fill word: [fill bit][counter]
                fill_word = (fill_value << 31) | fill_count
                result.append(fill_word)
                current_pos = next_pos
            else:
                # Literal word: [1][31-bit literal]
                literal = int.from_bytes(current_word.tobytes(), byteorder='big')
                literal_word = self.LITERAL_FLAG | literal
                result.append(literal_word)
                current_pos += self.WORD_SIZE
                
        return bytes(result)
        
    def decompress(self, data: bytes) -> bitarray:
        result = bitarray()
        
        for word in data:
            if word & self.LITERAL_FLAG:  # Literal word
                literal = word & ~self.LITERAL_FLAG
                bits = bitarray(bin(literal)[2:].zfill(self.WORD_SIZE - 1))
                result.extend(bits)
            else:  # Fill word
                fill_bit = bool(word & (1 << 30))
                count = word & ((1 << 30) - 1)
                result.extend([fill_bit] * (count * (self.WORD_SIZE - 1)))
                
        return result

class CONCISECompression(BitmapCompression):
    """Compressed 'N' Composable Integer Set compression."""
    
    WORD_SIZE = 32
    SEQUENCE_BIT = 0x80000000
    FILL_BIT = 0x40000000
    
    def compress(self, bitmap: bitarray) -> bytes:
        result = []
        current_pos = 0
        
        while current_pos < len(bitmap):
            # Find runs of consecutive 1s or 0s
            current_bit = bitmap[current_pos]
            run_length = 1
            pos = current_pos + 1
            
            while pos < len(bitmap) and bitmap[pos] == current_bit:
                run_length += 1
                pos += 1
                
            if run_length >= self.WORD_SIZE:
                # Encode as fill word
                words = run_length // self.WORD_SIZE
                remainder = run_length % self.WORD_SIZE
                
                fill_word = self.FILL_BIT | (int(current_bit) << 29) | words
                result.append(fill_word)
                
                if remainder:
                    # Add literal word for remainder
                    literal = int.from_bytes(bitmap[pos-remainder:pos].tobytes(), 
                                          byteorder='big')
                    result.append(self.SEQUENCE_BIT | literal)
            else:
                # Encode as literal word
                word_end = min(current_pos + self.WORD_SIZE, len(bitmap))
                literal = int.from_bytes(bitmap[current_pos:word_end].tobytes(),
                                      byteorder='big')
                result.append(self.SEQUENCE_BIT | literal)
                
            current_pos = pos
            
        return bytes(result)
        
    def decompress(self, data: bytes) -> bitarray:
        result = bitarray()
        
        for word in data:
            if word & self.SEQUENCE_BIT:  # Literal word
                literal = word & ~self.SEQUENCE_BIT
                bits = bitarray(bin(literal)[2:].zfill(self.WORD_SIZE - 1))
                result.extend(bits)
            else:  # Fill word
                fill_bit = bool(word & (1 << 29))
                count = word & ((1 << 29) - 1)
                result.extend([fill_bit] * (count * self.WORD_SIZE))
                
        return result

class RoaringBitmapCompression(BitmapCompression):
    """Roaring Bitmap compression implementation."""
    
    CONTAINER_SIZE = 2**16
    
    def __init__(self):
        self._containers: List[Tuple[int, List[int]]] = []  # (high bits, container)
        
    def compress(self, bitmap: bitarray) -> bytes:
        # Convert bitmap to list of set bit positions
        positions = [i for i, bit in enumerate(bitmap) if bit]
        
        # Group by high 16 bits
        containers: Dict[int, List[int]] = {}
        for pos in positions:
            high = pos >> 16
            low = pos & 0xFFFF
            if high not in containers:
                containers[high] = []
            containers[high].append(low)
            
        # Sort containers
        self._containers = sorted((high, lows) for high, lows in containers.items())
        
        # Serialize
        result = []
        result.append(len(self._containers).to_bytes(4, byteorder='big'))
        
        for high, lows in self._containers:
            result.append(high.to_bytes(2, byteorder='big'))
            result.append(len(lows).to_bytes(2, byteorder='big'))
            
            # Choose array or bitmap representation
            if len(lows) < 4096:  # Array is more efficient
                result.append(b'\x00')  # Array marker
                for low in sorted(lows):
                    result.append(low.to_bytes(2, byteorder='big'))
            else:  # Bitmap is more efficient
                result.append(b'\x01')  # Bitmap marker
                bitmap = bitarray('0' * 65536)
                for low in lows:
                    bitmap[low] = 1
                result.append(bitmap.tobytes())
                
        return b''.join(result)
        
    def decompress(self, data: bytes) -> bitarray:
        result = bitarray(self.CONTAINER_SIZE * len(self._containers))
        result.setall(0)
        
        pos = 0
        container_count = int.from_bytes(data[pos:pos+4], byteorder='big')
        pos += 4
        
        for _ in range(container_count):
            high = int.from_bytes(data[pos:pos+2], byteorder='big')
            pos += 2
            count = int.from_bytes(data[pos:pos+2], byteorder='big')
            pos += 2
            
            container_type = data[pos]
            pos += 1
            
            if container_type == 0:  # Array
                for _ in range(count):
                    low = int.from_bytes(data[pos:pos+2], byteorder='big')
                    pos += 2
                    position = (high << 16) | low
                    if position < len(result):
                        result[position] = 1
            else:  # Bitmap
                container_bits = bitarray()
                container_bits.frombytes(data[pos:pos+8192])
                pos += 8192
                
                for i, bit in enumerate(container_bits):
                    if bit:
                        position = (high << 16) | i
                        if position < len(result):
                            result[position] = 1
                            
        return result 

class CompressionAlgorithm(Enum):
    """Supported compression algorithms."""
    GZIP = "gz"
    LZMA = "xz"
    ZSTD = "zst"
    SNAPPY = "snappy"
    NONE = "raw"

class CompressionLevel(Enum):
    """Compression level presets."""
    FAST = "fast"
    BALANCED = "balanced"
    MAX = "max"

class CompressionOptimizer:
    """Handles compression optimization for incremental exports."""
    
    # Algorithm-specific compression levels
    COMPRESSION_LEVELS = {
        CompressionAlgorithm.GZIP: {
            CompressionLevel.FAST: 1,
            CompressionLevel.BALANCED: 6,
            CompressionLevel.MAX: 9
        },
        CompressionAlgorithm.LZMA: {
            CompressionLevel.FAST: 0,
            CompressionLevel.BALANCED: 6,
            CompressionLevel.MAX: 9
        },
        CompressionAlgorithm.ZSTD: {
            CompressionLevel.FAST: 1,
            CompressionLevel.BALANCED: 3,
            CompressionLevel.MAX: 22
        }
    }

    def __init__(
        self,
        algorithm: CompressionAlgorithm = CompressionAlgorithm.ZSTD,
        level: CompressionLevel = CompressionLevel.BALANCED,
        auto_select: bool = True
    ):
        self.algorithm = algorithm
        self.level = level
        self.auto_select = auto_select

    def compress_file(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Compress a file using the selected algorithm."""
        input_path = Path(input_path)
        if not output_path:
            output_path = input_path.with_suffix(f".{self.algorithm.value}")
        output_path = Path(output_path)

        # Auto-select algorithm if enabled
        if self.auto_select:
            self.algorithm = self._select_algorithm(input_path)
            output_path = output_path.with_suffix(f".{self.algorithm.value}")

        # Get compression level
        compression_level = self.COMPRESSION_LEVELS.get(
            self.algorithm, {}
        ).get(self.level)

        # Compress file
        input_size = os.path.getsize(input_path)
        try:
            if self.algorithm == CompressionAlgorithm.GZIP:
                with open(input_path, 'rb') as f_in:
                    with gzip.open(output_path, 'wb', compresslevel=compression_level) as f_out:
                        f_out.write(f_in.read())

            elif self.algorithm == CompressionAlgorithm.LZMA:
                with open(input_path, 'rb') as f_in:
                    with lzma.open(output_path, 'wb', preset=compression_level) as f_out:
                        f_out.write(f_in.read())

            elif self.algorithm == CompressionAlgorithm.ZSTD:
                with open(input_path, 'rb') as f_in:
                    data = f_in.read()
                    compressed = zstd.compress(data, compression_level)
                    with open(output_path, 'wb') as f_out:
                        f_out.write(compressed)

            elif self.algorithm == CompressionAlgorithm.SNAPPY:
                with open(input_path, 'rb') as f_in:
                    data = f_in.read()
                    compressed = snappy.compress(data)
                    with open(output_path, 'wb') as f_out:
                        f_out.write(compressed)

            else:  # NONE
                import shutil
                shutil.copy2(input_path, output_path)

        except Exception as e:
            logger.error(f"Compression failed: {e}")
            raise

        # Calculate compression stats
        output_size = os.path.getsize(output_path)
        compression_ratio = input_size / output_size if output_size > 0 else 0

        compression_info = {
            "algorithm": self.algorithm.value,
            "level": self.level.value,
            "input_size": input_size,
            "output_size": output_size,
            "compression_ratio": compression_ratio
        }

        if metadata:
            compression_info.update(metadata)

        return compression_info

    def decompress_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path]
    ) -> None:
        """Decompress a file."""
        input_path = Path(input_path)
        output_path = Path(output_path)

        # Detect algorithm from file extension
        algorithm = CompressionAlgorithm(input_path.suffix[1:])

        try:
            if algorithm == CompressionAlgorithm.GZIP:
                with gzip.open(input_path, 'rb') as f_in:
                    with open(output_path, 'wb') as f_out:
                        f_out.write(f_in.read())

            elif algorithm == CompressionAlgorithm.LZMA:
                with lzma.open(input_path, 'rb') as f_in:
                    with open(output_path, 'wb') as f_out:
                        f_out.write(f_in.read())

            elif algorithm == CompressionAlgorithm.ZSTD:
                with open(input_path, 'rb') as f_in:
                    data = f_in.read()
                    decompressed = zstd.decompress(data)
                    with open(output_path, 'wb') as f_out:
                        f_out.write(decompressed)

            elif algorithm == CompressionAlgorithm.SNAPPY:
                with open(input_path, 'rb') as f_in:
                    data = f_in.read()
                    decompressed = snappy.decompress(data)
                    with open(output_path, 'wb') as f_out:
                        f_out.write(decompressed)

            else:  # NONE
                import shutil
                shutil.copy2(input_path, output_path)

        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            raise

    def _select_algorithm(self, input_path: Path) -> CompressionAlgorithm:
        """Auto-select best compression algorithm based on file characteristics."""
        # Read sample of file content
        sample_size = min(os.path.getsize(input_path), 1024 * 1024)  # Max 1MB sample
        with open(input_path, 'rb') as f:
            sample = f.read(sample_size)

        # Analyze content type
        try:
            # Try to parse as JSON to detect structured data
            json.loads(sample.decode('utf-8'))
            # Structured data typically compresses well with ZSTD
            return CompressionAlgorithm.ZSTD
        except:
            pass

        # Calculate entropy of sample
        entropy = self._calculate_entropy(sample)

        # Select algorithm based on entropy and file size
        file_size = os.path.getsize(input_path)

        if entropy > 7.5:  # High entropy (already compressed or encrypted)
            return CompressionAlgorithm.NONE
        elif file_size < 1024 * 1024:  # Small files (<1MB)
            return CompressionAlgorithm.SNAPPY  # Fast compression
        elif entropy < 4.0:  # Low entropy (highly compressible)
            return CompressionAlgorithm.LZMA  # Best compression
        else:  # Medium entropy
            return CompressionAlgorithm.ZSTD  # Good balance

    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data."""
        if not data:
            return 0.0

        # Count byte frequencies
        frequencies = {}
        for byte in data:
            frequencies[byte] = frequencies.get(byte, 0) + 1

        # Calculate entropy
        entropy = 0
        for count in frequencies.values():
            probability = count / len(data)
            entropy -= probability * (probability.bit_length() - 1)

        return entropy