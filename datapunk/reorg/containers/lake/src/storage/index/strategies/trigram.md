# Trigram Strategy Module Documentation

## Purpose

This module implements a trigram-based text search strategy using the GiST index framework. It enables efficient text similarity searches by breaking text into three-character sequences (trigrams) and using set operations for comparisons.

## Implementation

### Core Components

1. **TrigramSet Class** [Lines: 6-41]

   - Represents a set of trigrams extracted from text
   - Key attributes:
     - trigrams: Set of three-character sequences
     - compressed: Flag indicating compression state
   - Methods:
     - `from_text()`: Creates trigram set from input text
     - `similarity()`: Calculates Jaccard similarity
     - `contains()`: Checks trigram subset relationship
     - `compress()`: Creates compressed representation

2. **TrigramStrategy Class** [Lines: 43-152]
   - Implements GiST predicate strategy for trigram indexing
   - Key methods:
     - `consistent()`: Checks entry consistency with query
     - `union()`: Creates union of trigram sets
     - `compress()/decompress()`: Handles compression
     - `penalty()`: Calculates insertion penalties
     - `pick_split()`: Splits entries for tree balancing

### Key Features

1. **Text Processing** [Lines: 12-18]

   - Padding for edge trigrams
   - Set-based trigram extraction
   - Efficient text comparison

2. **Similarity Metrics** [Lines: 20-31]

   - Jaccard similarity calculation
   - Containment checking
   - Threshold-based matching

3. **Compression Support** [Lines: 33-41]
   - Random sampling for large sets
   - Size-limited compression
   - Lossy compression strategy

## Dependencies

### Required Packages

- typing: Type hints
- dataclasses: Data structure decorators
- numpy: Random sampling and numerical operations

### Internal Modules

- gist: GiST index implementation
- GiSTPredicateStrategy: Base strategy class

## Known Issues

1. **Compression Limitations**

   - Lossy compression may affect accuracy
   - Random sampling might miss important trigrams
   - No recovery of original trigrams after compression

2. **Performance Trade-offs**
   - Memory usage vs. compression ratio
   - Similarity threshold affects false positives
   - Large text inputs create many trigrams

## Performance Considerations

1. **Memory Usage**

   - Set-based storage for trigrams
   - Compression for large trigram sets
   - Union operations may create large sets

2. **Search Efficiency**
   - Fast set operations for comparisons
   - Early filtering with similarity threshold
   - Compressed sets reduce memory but affect accuracy

## Security Considerations

1. **Input Validation**
   - Text size limits needed
   - Resource monitoring for large inputs
   - Memory allocation controls

## Trade-offs and Design Decisions

1. **Trigram Approach**

   - Decision: Use three-character sequences
   - Rationale: Balance between precision and storage
   - Trade-off: Granularity vs. index size

2. **Compression Strategy**

   - Decision: Random sampling for large sets
   - Rationale: Simple and effective size reduction
   - Trade-off: Accuracy vs. memory usage

3. **Similarity Threshold**
   - Decision: Configurable similarity threshold
   - Rationale: Allows tuning for different use cases
   - Trade-off: Precision vs. recall

## Future Improvements

1. Add weighted trigram selection
2. Implement non-lossy compression
3. Add trigram frequency analysis
4. Support variable-length n-grams
5. Add caching for frequent queries
6. Implement parallel processing for large texts
