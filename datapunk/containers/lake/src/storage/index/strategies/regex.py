from typing import List, Tuple, Set, Any, Optional
from dataclasses import dataclass
import re
import numpy as np
from ..gist import GiSTPredicateStrategy

@dataclass
class RegexPattern:
    """Regular expression pattern with optimization features."""
    pattern: str
    prefix: str  # Common prefix for faster filtering
    suffix: str  # Common suffix for faster filtering
    literals: Set[str]  # Required literal strings
    is_case_sensitive: bool
    min_length: int  # Minimum length of matching strings
    max_length: Optional[int]  # Maximum length of matching strings, if known
    
    @staticmethod
    def from_regex(pattern: str, is_case_sensitive: bool = True) -> 'RegexPattern':
        """Create a RegexPattern from a regular expression string."""
        # Analyze pattern for optimization opportunities
        prefix = ""
        suffix = ""
        literals = set()
        min_length = 0
        max_length = None
        
        # Extract literal prefix
        match = re.match(r'^[a-zA-Z0-9]+', pattern)
        if match:
            prefix = match.group(0)
            
        # Extract literal suffix
        match = re.search(r'[a-zA-Z0-9]+$', pattern)
        if match:
            suffix = match.group(0)
            
        # Extract required literals
        for match in re.finditer(r'[a-zA-Z0-9]+', pattern):
            literals.add(match.group(0))
            
        # Calculate minimum length
        parts = re.split(r'[*+?{}]', pattern)
        min_length = sum(len(p) for p in parts if not any(c in '()|[]' for c in p))
        
        # Try to determine maximum length
        if not any(c in '*+' for c in pattern):
            # Pattern has no unbounded repetition
            max_parts = []
            for part in re.findall(r'{(\d+)}', pattern):
                max_parts.append(int(part))
            if max_parts:
                max_length = sum(max_parts) + len(pattern) - sum(len(str(p)) + 2 for p in max_parts)
                
        return RegexPattern(
            pattern=pattern,
            prefix=prefix,
            suffix=suffix,
            literals=literals,
            is_case_sensitive=is_case_sensitive,
            min_length=min_length,
            max_length=max_length
        )
        
    def matches(self, text: str) -> bool:
        """Check if text matches the pattern."""
        # Quick checks first
        if len(text) < self.min_length:
            return False
        if self.max_length and len(text) > self.max_length:
            return False
            
        # Check prefix/suffix
        if self.prefix:
            if self.is_case_sensitive:
                if not text.startswith(self.prefix):
                    return False
            else:
                if not text.lower().startswith(self.prefix.lower()):
                    return False
                    
        if self.suffix:
            if self.is_case_sensitive:
                if not text.endswith(self.suffix):
                    return False
            else:
                if not text.lower().endswith(self.suffix.lower()):
                    return False
                    
        # Check required literals
        if self.literals:
            text_lower = text.lower() if not self.is_case_sensitive else text
            for literal in self.literals:
                literal_check = literal.lower() if not self.is_case_sensitive else literal
                if literal_check not in text_lower:
                    return False
                    
        # Finally, do full regex match
        flags = 0 if self.is_case_sensitive else re.IGNORECASE
        return bool(re.search(self.pattern, text, flags))
        
    def could_match(self, other: 'RegexPattern') -> bool:
        """Check if this pattern could match strings matching other pattern."""
        # If other pattern requires longer strings than our maximum, no match possible
        if self.max_length and other.min_length > self.max_length:
            return False
            
        # If other pattern has a shorter maximum than our minimum, no match possible
        if other.max_length and self.min_length > other.max_length:
            return False
            
        # If we have a prefix and other has a different prefix, no match possible
        if self.prefix and other.prefix:
            if self.is_case_sensitive and other.is_case_sensitive:
                if not (self.prefix.startswith(other.prefix) or 
                        other.prefix.startswith(self.prefix)):
                    return False
            else:
                prefix1 = self.prefix.lower()
                prefix2 = other.prefix.lower()
                if not (prefix1.startswith(prefix2) or prefix2.startswith(prefix1)):
                    return False
                    
        # Similar check for suffix
        if self.suffix and other.suffix:
            if self.is_case_sensitive and other.is_case_sensitive:
                if not (self.suffix.endswith(other.suffix) or 
                        other.suffix.endswith(self.suffix)):
                    return False
            else:
                suffix1 = self.suffix.lower()
                suffix2 = other.suffix.lower()
                if not (suffix1.endswith(suffix2) or suffix2.endswith(suffix1)):
                    return False
                    
        # If patterns share no literals, they might still match
        return True

class RegexStrategy(GiSTPredicateStrategy[RegexPattern]):
    """GiST predicate strategy for regular expression search."""
    
    def __init__(self, compression_threshold: int = 100):
        self.compression_threshold = compression_threshold
        
    def consistent(self, entry: RegexPattern, query: Any) -> bool:
        """Check if entry is consistent with query."""
        if isinstance(query, str):
            # Direct string match
            return entry.matches(query)
        elif isinstance(query, RegexPattern):
            # Pattern intersection check
            return entry.could_match(query)
        return False
        
    def union(self, entries: List[RegexPattern]) -> RegexPattern:
        """Create union pattern that matches any of the entries."""
        if not entries:
            return RegexPattern.from_regex(".*")
            
        # Find common prefix and suffix
        prefix = entries[0].prefix
        suffix = entries[0].suffix
        literals = set(entries[0].literals)
        min_length = entries[0].min_length
        max_length = entries[0].max_length
        is_case_sensitive = all(e.is_case_sensitive for e in entries)
        
        for entry in entries[1:]:
            # Update prefix
            while prefix and not entry.prefix.startswith(prefix):
                prefix = prefix[:-1]
                
            # Update suffix
            while suffix and not entry.suffix.endswith(suffix):
                suffix = suffix[1:]
                
            # Update literals to those common to all entries
            literals &= entry.literals
            
            # Update length bounds
            min_length = min(min_length, entry.min_length)
            if max_length is not None:
                if entry.max_length is None:
                    max_length = None
                else:
                    max_length = max(max_length, entry.max_length)
                    
        # Create combined pattern
        patterns = [e.pattern for e in entries]
        combined = f"({'|'.join(patterns)})"
        
        return RegexPattern(
            pattern=combined,
            prefix=prefix,
            suffix=suffix,
            literals=literals,
            is_case_sensitive=is_case_sensitive,
            min_length=min_length,
            max_length=max_length
        )
        
    def compress(self, entry: RegexPattern) -> RegexPattern:
        """Compress a regex pattern by simplifying it."""
        if len(entry.pattern) <= self.compression_threshold:
            return entry
            
        # Create a simpler pattern that contains the essential constraints
        compressed = []
        
        if entry.prefix:
            compressed.append(re.escape(entry.prefix))
            compressed.append(".*")
            
        if entry.literals - {entry.prefix, entry.suffix}:
            # Add required literals with flexible positioning
            literals = sorted(entry.literals - {entry.prefix, entry.suffix})
            for literal in literals[:3]:  # Limit to 3 literals for compression
                compressed.append(f"(?=.*{re.escape(literal)})")
                
        if entry.suffix:
            compressed.append(".*")
            compressed.append(re.escape(entry.suffix))
            
        if not compressed:
            compressed = [".*"]
            
        return RegexPattern(
            pattern="".join(compressed),
            prefix=entry.prefix,
            suffix=entry.suffix,
            literals=entry.literals,
            is_case_sensitive=entry.is_case_sensitive,
            min_length=entry.min_length,
            max_length=None  # Compressed pattern loses max length info
        )
        
    def decompress(self, entry: RegexPattern) -> RegexPattern:
        """Decompress a regex pattern (no-op as compression is lossy)."""
        return entry
        
    def penalty(self, entry1: RegexPattern, entry2: RegexPattern) -> float:
        """Calculate penalty for inserting entry2 into entry1's subtree."""
        penalty = 0
        
        # Penalty for different prefixes
        if entry1.prefix:
            if not entry2.prefix.startswith(entry1.prefix):
                penalty += len(entry1.prefix)
                
        # Penalty for different suffixes
        if entry1.suffix:
            if not entry2.suffix.endswith(entry1.suffix):
                penalty += len(entry1.suffix)
                
        # Penalty for non-overlapping literals
        common_literals = entry1.literals & entry2.literals
        all_literals = entry1.literals | entry2.literals
        if all_literals:
            penalty += len(all_literals - common_literals) / len(all_literals)
            
        # Penalty for length differences
        if entry1.max_length and entry2.min_length > entry1.max_length:
            penalty += entry2.min_length - entry1.max_length
            
        return penalty
        
    def pick_split(self, entries: List[RegexPattern]) -> Tuple[List[RegexPattern], List[RegexPattern]]:
        """Split entries into two groups."""
        if len(entries) <= 2:
            return [entries[0]], entries[1:]
            
        # Find two most different patterns as seeds
        max_penalty = -1
        seeds = (0, 1)
        
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                penalty = self.penalty(entries[i], entries[j])
                if penalty > max_penalty:
                    max_penalty = penalty
                    seeds = (i, j)
                    
        # Distribute entries to closest seed
        group1 = [entries[seeds[0]]]
        group2 = [entries[seeds[1]]]
        
        for i, entry in enumerate(entries):
            if i not in seeds:
                penalty1 = self.penalty(group1[0], entry)
                penalty2 = self.penalty(group2[0], entry)
                
                if penalty1 < penalty2:
                    group1.append(entry)
                else:
                    group2.append(entry)
                    
        # Ensure minimum fill
        while len(group1) < 2 and group2:
            group1.append(group2.pop())
        while len(group2) < 2 and group1:
            group2.append(group1.pop())
            
        return group1, group2

def create_regex_index(
    name: str,
    table_name: str,
    column: str,
    compression_threshold: int = 100
) -> 'GiSTIndex[RegexPattern, Any]':
    """Helper function to create a regex-based GiST index."""
    from ..gist import GiSTIndex
    
    strategy = RegexStrategy(compression_threshold=compression_threshold)
    return GiSTIndex(
        name=name,
        table_name=table_name,
        columns=[column],
        predicate_strategy=strategy
    ) 