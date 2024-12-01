from typing import Any, Dict, List, Optional, Set, Tuple
from bitarray import bitarray
from .core import Index, IndexType
from .compression import BitmapCompression, WAHCompression, CONCISECompression, RoaringBitmapCompression

class CompressionType:
    NONE = "none"
    WAH = "wah"
    CONCISE = "concise"
    ROARING = "roaring"

class BitmapIndex(Index):
    """Bitmap index implementation optimized for low-cardinality columns."""
    
    def __init__(self, name: str, table_name: str, column_names: List[str], 
                 compression_type: str = CompressionType.NONE):
        super().__init__(name, table_name, column_names, IndexType.BITMAP)
        self._bitmaps: Dict[Any, bitarray] = {}
        self._compressed_bitmaps: Dict[Any, bytes] = {}
        self._row_count: int = 0
        self._deleted_rows: Set[int] = set()
        self._compression_type = compression_type
        self._compressor = self._get_compressor(compression_type)
        
    def _get_compressor(self, compression_type: str) -> Optional[BitmapCompression]:
        """Get the appropriate compressor based on type."""
        if compression_type == CompressionType.WAH:
            return WAHCompression()
        elif compression_type == CompressionType.CONCISE:
            return CONCISECompression()
        elif compression_type == CompressionType.ROARING:
            return RoaringBitmapCompression()
        return None
        
    def insert(self, key: Any, row_id: int) -> None:
        """Insert a new key-value pair into the bitmap index."""
        if row_id >= self._row_count:
            self._extend_bitmaps(row_id + 1)
            
        if key not in self._bitmaps:
            self._bitmaps[key] = bitarray('0' * self._row_count)
            
        self._bitmaps[key][row_id] = 1
        
        if row_id in self._deleted_rows:
            self._deleted_rows.remove(row_id)
            
        # Update compression if enabled
        if self._compressor:
            self._compressed_bitmaps[key] = self._compressor.compress(self._bitmaps[key])
            
    def delete(self, key: Any, row_id: int) -> None:
        """Remove a key-value pair from the bitmap index."""
        if key in self._bitmaps and row_id < self._row_count:
            self._bitmaps[key][row_id] = 0
            self._deleted_rows.add(row_id)
            
            # Update compression if enabled
            if self._compressor:
                self._compressed_bitmaps[key] = self._compressor.compress(self._bitmaps[key])
                
    def search(self, key: Any) -> List[int]:
        """Search for all row IDs matching the given key."""
        if key not in self._bitmaps:
            return []
            
        bitmap = self._get_bitmap(key)
        return [i for i, bit in enumerate(bitmap) if bit and i not in self._deleted_rows]
        
    def _get_bitmap(self, key: Any) -> bitarray:
        """Get bitmap, decompressing if necessary."""
        if not self._compressor:
            return self._bitmaps[key]
        return self._compressor.decompress(self._compressed_bitmaps[key])
        
    def range_search(self, start_key: Any, end_key: Any) -> List[int]:
        """Perform a range search using bitmap operations."""
        result = bitarray('0' * self._row_count)
        
        for key in self._bitmaps:
            if start_key <= key <= end_key:
                bitmap = self._get_bitmap(key)
                result |= bitmap
                
        return [i for i, bit in enumerate(result) if bit and i not in self._deleted_rows]
        
    def _extend_bitmaps(self, new_size: int) -> None:
        """Extend all bitmaps to accommodate new rows."""
        extension_size = new_size - self._row_count
        if extension_size <= 0:
            return
            
        for bitmap in self._bitmaps.values():
            bitmap.extend('0' * extension_size)
            
        self._row_count = new_size
        
        # Update compression if enabled
        if self._compressor:
            for key, bitmap in self._bitmaps.items():
                self._compressed_bitmaps[key] = self._compressor.compress(bitmap)
                
    def rebuild(self) -> None:
        """Rebuild the bitmap index to reclaim space from deleted rows."""
        if not self._deleted_rows:
            return
            
        new_size = self._row_count - len(self._deleted_rows)
        new_bitmaps: Dict[Any, bitarray] = {}
        
        for key, old_bitmap in self._bitmaps.items():
            new_bitmap = bitarray()
            new_bitmap.extend(bit for i, bit in enumerate(old_bitmap)
                            if i not in self._deleted_rows)
            new_bitmaps[key] = new_bitmap
            
        self._bitmaps = new_bitmaps
        self._row_count = new_size
        self._deleted_rows.clear()
        
        # Update compression if enabled
        if self._compressor:
            self._compressed_bitmaps.clear()
            for key, bitmap in self._bitmaps.items():
                self._compressed_bitmaps[key] = self._compressor.compress(bitmap)
                
    def get_statistics(self) -> Dict[str, Any]:
        """Return statistics about the bitmap index."""
        total_bits = sum(bitmap.count(1) for bitmap in self._bitmaps.values())
        stats = {
            "distinct_values": len(self._bitmaps),
            "total_bits_set": total_bits,
            "density": total_bits / (self._row_count * len(self._bitmaps)) if self._bitmaps else 0,
            "deleted_rows": len(self._deleted_rows),
            "total_rows": self._row_count,
            "compression_type": self._compression_type
        }
        
        if self._compressor:
            compressed_size = sum(len(data) for data in self._compressed_bitmaps.values())
            uncompressed_size = sum(len(bitmap.tobytes()) for bitmap in self._bitmaps.values())
            stats.update({
                "compression_ratio": compressed_size / uncompressed_size if uncompressed_size > 0 else 1.0,
                "compressed_size_bytes": compressed_size,
                "uncompressed_size_bytes": uncompressed_size
            })
            
        return stats