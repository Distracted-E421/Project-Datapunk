from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from bitarray import bitarray

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