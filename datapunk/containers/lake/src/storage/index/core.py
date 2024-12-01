from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Union, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum, auto
import json
import threading
from datetime import datetime

K = TypeVar('K')  # Key type
V = TypeVar('V')  # Value type

class IndexType(Enum):
    """Types of supported indexes."""
    BTREE = auto()
    HASH = auto()
    BITMAP = auto()
    RTREE = auto()  # For spatial data

@dataclass
class IndexStats:
    """Statistics for an index."""
    total_entries: int
    depth: int
    size_bytes: int
    last_updated: datetime
    read_count: int
    write_count: int
    avg_lookup_time_ms: float
    avg_insert_time_ms: float

@dataclass
class IndexMetadata:
    """Metadata for an index."""
    name: str
    index_type: IndexType
    key_type: str
    value_type: str
    is_unique: bool
    is_primary: bool
    columns: List[str]
    stats: IndexStats
    properties: Dict[str, Any]

class Index(ABC, Generic[K, V]):
    """Base class for all index implementations."""
    
    def __init__(
        self,
        name: str,
        key_type: str,
        value_type: str,
        is_unique: bool = False,
        is_primary: bool = False,
        properties: Dict[str, Any] = None
    ):
        self.name = name
        self.key_type = key_type
        self.value_type = value_type
        self.is_unique = is_unique
        self.is_primary = is_primary
        self.properties = properties or {}
        self.stats = IndexStats(
            total_entries=0,
            depth=0,
            size_bytes=0,
            last_updated=datetime.now(),
            read_count=0,
            write_count=0,
            avg_lookup_time_ms=0.0,
            avg_insert_time_ms=0.0
        )
        self._lock = threading.RLock()
        
    @abstractmethod
    def insert(self, key: K, value: V) -> None:
        """Insert a key-value pair into the index."""
        pass
        
    @abstractmethod
    def delete(self, key: K) -> None:
        """Delete a key from the index."""
        pass
        
    @abstractmethod
    def search(self, key: K) -> Optional[V]:
        """Search for a value by key."""
        pass
        
    @abstractmethod
    def range_search(self, start_key: K, end_key: K) -> List[V]:
        """Search for values in a key range."""
        pass
        
    @abstractmethod
    def clear(self) -> None:
        """Clear all entries from the index."""
        pass
        
    def get_metadata(self) -> IndexMetadata:
        """Get index metadata."""
        return IndexMetadata(
            name=self.name,
            index_type=self._get_index_type(),
            key_type=self.key_type,
            value_type=self.value_type,
            is_unique=self.is_unique,
            is_primary=self.is_primary,
            columns=self._get_indexed_columns(),
            stats=self.stats,
            properties=self.properties
        )
        
    @abstractmethod
    def _get_index_type(self) -> IndexType:
        """Get the type of this index."""
        pass
        
    @abstractmethod
    def _get_indexed_columns(self) -> List[str]:
        """Get the columns covered by this index."""
        pass
        
    def update_stats(
        self,
        operation: str,
        duration_ms: float
    ) -> None:
        """Update index statistics."""
        with self._lock:
            if operation == 'read':
                self.stats.read_count += 1
                self.stats.avg_lookup_time_ms = (
                    (self.stats.avg_lookup_time_ms * (self.stats.read_count - 1) +
                     duration_ms) / self.stats.read_count
                )
            elif operation == 'write':
                self.stats.write_count += 1
                self.stats.avg_insert_time_ms = (
                    (self.stats.avg_insert_time_ms * (self.stats.write_count - 1) +
                     duration_ms) / self.stats.write_count
                )
            self.stats.last_updated = datetime.now()

class IndexManager:
    """Manages index creation and maintenance."""
    
    def __init__(self):
        self.indexes: Dict[str, Index] = {}
        self._lock = threading.RLock()
        
    def create_index(
        self,
        name: str,
        index_type: IndexType,
        key_type: str,
        value_type: str,
        is_unique: bool = False,
        is_primary: bool = False,
        properties: Dict[str, Any] = None
    ) -> Index:
        """Create a new index."""
        with self._lock:
            if name in self.indexes:
                raise ValueError(f"Index {name} already exists")
                
            index = self._create_index_instance(
                name,
                index_type,
                key_type,
                value_type,
                is_unique,
                is_primary,
                properties
            )
            self.indexes[name] = index
            return index
            
    def drop_index(self, name: str) -> None:
        """Drop an index."""
        with self._lock:
            if name not in self.indexes:
                raise ValueError(f"Index {name} does not exist")
                
            index = self.indexes[name]
            index.clear()
            del self.indexes[name]
            
    def get_index(self, name: str) -> Optional[Index]:
        """Get an index by name."""
        return self.indexes.get(name)
        
    def list_indexes(self) -> List[IndexMetadata]:
        """List all indexes."""
        return [index.get_metadata() for index in self.indexes.values()]
        
    def get_index_stats(self, name: str) -> Optional[IndexStats]:
        """Get statistics for an index."""
        index = self.get_index(name)
        return index.stats if index else None
        
    def optimize_index(self, name: str) -> None:
        """Optimize an index."""
        index = self.get_index(name)
        if not index:
            raise ValueError(f"Index {name} does not exist")
            
        # Trigger index-specific optimization
        if hasattr(index, 'optimize'):
            index.optimize()
            
    def _create_index_instance(
        self,
        name: str,
        index_type: IndexType,
        key_type: str,
        value_type: str,
        is_unique: bool,
        is_primary: bool,
        properties: Dict[str, Any]
    ) -> Index:
        """Create appropriate index instance based on type."""
        from .btree import BTreeIndex
        from .hash import HashIndex
        from .bitmap import BitmapIndex
        from .rtree import RTreeIndex
        
        index_classes = {
            IndexType.BTREE: BTreeIndex,
            IndexType.HASH: HashIndex,
            IndexType.BITMAP: BitmapIndex,
            IndexType.RTREE: RTreeIndex
        }
        
        index_class = index_classes.get(index_type)
        if not index_class:
            raise ValueError(f"Unsupported index type: {index_type}")
            
        return index_class(
            name=name,
            key_type=key_type,
            value_type=value_type,
            is_unique=is_unique,
            is_primary=is_primary,
            properties=properties
        ) 