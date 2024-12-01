from typing import Any, Dict, List, Optional, Tuple
from .core import Index, IndexType

class HashIndex(Index):
    """Hash-based index implementation optimized for equality searches."""
    
    def __init__(self, name: str, table_name: str, column_names: List[str]):
        super().__init__(name, table_name, column_names, IndexType.HASH)
        self._index: Dict[Any, List[int]] = {}  # Hash table mapping values to row IDs
        self._collision_chains: Dict[int, List[int]] = {}  # Handle hash collisions
        
    def insert(self, key: Any, row_id: int) -> None:
        """Insert a new key-value pair into the hash index."""
        hash_val = hash(key)
        if hash_val not in self._index:
            self._index[hash_val] = []
        
        if key not in self._collision_chains:
            self._collision_chains[hash_val] = []
            
        self._index[hash_val].append(row_id)
        self._collision_chains[hash_val].append(key)
        
    def delete(self, key: Any, row_id: int) -> None:
        """Remove a key-value pair from the hash index."""
        hash_val = hash(key)
        if hash_val in self._index:
            try:
                idx = self._index[hash_val].index(row_id)
                self._index[hash_val].pop(idx)
                self._collision_chains[hash_val].pop(idx)
                
                if not self._index[hash_val]:
                    del self._index[hash_val]
                    del self._collision_chains[hash_val]
            except ValueError:
                pass
                
    def search(self, key: Any) -> List[int]:
        """Search for all row IDs matching the given key."""
        hash_val = hash(key)
        if hash_val not in self._index:
            return []
            
        # Handle hash collisions by checking actual keys
        result = []
        for idx, stored_key in enumerate(self._collision_chains[hash_val]):
            if stored_key == key:
                result.append(self._index[hash_val][idx])
        return result
        
    def range_search(self, start_key: Any, end_key: Any) -> List[int]:
        """Hash indexes don't support efficient range searches."""
        raise NotImplementedError("Hash indexes don't support range searches")
        
    def rebuild(self) -> None:
        """Rebuild the hash index to optimize space usage."""
        # Create new structures
        new_index: Dict[Any, List[int]] = {}
        new_chains: Dict[int, List[int]] = {}
        
        # Rebuild by reinserting all entries
        for hash_val, row_ids in self._index.items():
            for idx, row_id in enumerate(row_ids):
                key = self._collision_chains[hash_val][idx]
                if hash_val not in new_index:
                    new_index[hash_val] = []
                    new_chains[hash_val] = []
                new_index[hash_val].append(row_id)
                new_chains[hash_val].append(key)
                
        self._index = new_index
        self._collision_chains = new_chains
        
    def get_statistics(self) -> Dict[str, Any]:
        """Return statistics about the hash index."""
        return {
            "total_entries": sum(len(v) for v in self._index.values()),
            "unique_keys": len(self._index),
            "collision_rate": sum(1 for v in self._index.values() if len(v) > 1) / len(self._index) if self._index else 0,
            "max_chain_length": max((len(v) for v in self._index.values()), default=0)
        } 