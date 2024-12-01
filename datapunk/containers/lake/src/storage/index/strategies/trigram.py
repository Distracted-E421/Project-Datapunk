from typing import List, Tuple, Set, Any
from dataclasses import dataclass
import numpy as np
from ..gist import GiSTPredicateStrategy

@dataclass
class TrigramSet:
    """Set of trigrams with optional compression."""
    trigrams: Set[str]
    compressed: bool = False
    
    @staticmethod
    def from_text(text: str) -> 'TrigramSet':
        """Create a trigram set from text."""
        # Pad text for edge trigrams
        padded = f"  {text}  "
        trigrams = {padded[i:i+3] for i in range(len(padded)-2)}
        return TrigramSet(trigrams)
    
    def similarity(self, other: 'TrigramSet') -> float:
        """Calculate Jaccard similarity between trigram sets."""
        if not self.trigrams or not other.trigrams:
            return 0.0
        intersection = len(self.trigrams & other.trigrams)
        union = len(self.trigrams | other.trigrams)
        return intersection / union if union > 0 else 0.0
    
    def contains(self, other: 'TrigramSet') -> bool:
        """Check if this set contains all trigrams from other set."""
        return other.trigrams.issubset(self.trigrams)
    
    def compress(self, max_trigrams: int = 100) -> 'TrigramSet':
        """Create a compressed version with limited number of trigrams."""
        if len(self.trigrams) <= max_trigrams:
            return self
            
        # Select most representative trigrams
        trigrams = list(self.trigrams)
        selected = set(np.random.choice(trigrams, max_trigrams, replace=False))
        return TrigramSet(selected, compressed=True)

class TrigramStrategy(GiSTPredicateStrategy[TrigramSet]):
    """GiST predicate strategy for trigram-based text search."""
    
    def __init__(self, similarity_threshold: float = 0.3):
        self.similarity_threshold = similarity_threshold
        
    def consistent(self, entry: TrigramSet, query: Any) -> bool:
        """Check if entry is consistent with query."""
        if not isinstance(query, (str, TrigramSet)):
            return False
            
        if isinstance(query, str):
            query = TrigramSet.from_text(query)
            
        # If entry is compressed, we need to be more lenient
        if entry.compressed:
            # Use similarity threshold for compressed entries
            return entry.similarity(query) >= self.similarity_threshold
        else:
            # For uncompressed entries, use exact containment
            return entry.contains(query)
            
    def union(self, entries: List[TrigramSet]) -> TrigramSet:
        """Create union of multiple trigram sets."""
        if not entries:
            return TrigramSet(set())
            
        # Union all trigrams
        union_trigrams = set.union(*(e.trigrams for e in entries))
        
        # Compress if too large
        result = TrigramSet(union_trigrams)
        if len(union_trigrams) > 100:
            result = result.compress()
            
        return result
        
    def compress(self, entry: TrigramSet) -> TrigramSet:
        """Compress a trigram set."""
        return entry.compress()
        
    def decompress(self, entry: TrigramSet) -> TrigramSet:
        """Decompress a trigram set (no-op as compression is lossy)."""
        return entry
        
    def penalty(self, entry1: TrigramSet, entry2: TrigramSet) -> float:
        """Calculate penalty for inserting entry2 into entry1's subtree."""
        # Calculate how many new trigrams would need to be added
        if not entry1.trigrams:
            return len(entry2.trigrams)
            
        additional_trigrams = len(entry2.trigrams - entry1.trigrams)
        return additional_trigrams
        
    def pick_split(self, entries: List[TrigramSet]) -> Tuple[List[TrigramSet], List[TrigramSet]]:
        """Split entries into two groups using clustering."""
        if len(entries) <= 2:
            return [entries[0]], entries[1:]
            
        # Use k-means like approach with trigram similarity
        # First, pick two entries that are most dissimilar
        max_dist = -1
        seeds = (0, 1)
        
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                similarity = entries[i].similarity(entries[j])
                distance = 1 - similarity
                if distance > max_dist:
                    max_dist = distance
                    seeds = (i, j)
                    
        # Assign each entry to the closest seed
        group1 = [entries[seeds[0]]]
        group2 = [entries[seeds[1]]]
        
        for i, entry in enumerate(entries):
            if i not in seeds:
                # Calculate average similarity to each group
                sim1 = np.mean([entry.similarity(e) for e in group1])
                sim2 = np.mean([entry.similarity(e) for e in group2])
                
                if sim1 > sim2:
                    group1.append(entry)
                else:
                    group2.append(entry)
                    
        # Ensure minimum fill
        while len(group1) < 2 and group2:
            group1.append(group2.pop())
        while len(group2) < 2 and group1:
            group2.append(group1.pop())
            
        return group1, group2

def create_trigram_index(
    name: str,
    table_name: str,
    column: str,
    similarity_threshold: float = 0.3
) -> 'GiSTIndex[TrigramSet, Any]':
    """Helper function to create a trigram-based GiST index."""
    from ..gist import GiSTIndex
    
    strategy = TrigramStrategy(similarity_threshold=similarity_threshold)
    return GiSTIndex(
        name=name,
        table_name=table_name,
        columns=[column],
        predicate_strategy=strategy
    ) 