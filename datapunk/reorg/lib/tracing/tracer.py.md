## Purpose

This module implements a comprehensive distributed tracing system for Datapunk's service mesh, providing both synchronous and asynchronous tracing capabilities with sampling, span management, and trace export functionality.

## Implementation

### Core Components

1. **SpanKind Enum** [Lines: 15-20]

   - Defines trace span categories
   - Supports internal, server, client, producer, consumer types
   - Used for span classification

2. **SpanContext Class** [Lines: 22-28]

   - Manages trace context data
   - Handles parent-child relationships
   - Supports distributed tracing baggage
   - Controls sampling decisions

3. **Span Class** [Lines: 30-40]

   - Core tracing data structure
   - Tracks timing and metadata
   - Manages events and attributes
   - Handles status information

4. **Sampler Class** [Lines: 42-60]

   - Controls trace sampling rates
   - Implements probabilistic sampling
   - Uses trace ID for consistency
   - Configurable sample rates

5. **SpanProcessor Class** [Lines: 62-110]

   - Processes span lifecycle events
   - Thread-safe span storage
   - Trace data management
   - JSON export capabilities

6. **Tracer Class** [Lines: 112-204]

   - Main tracing interface
   - Span lifecycle management
   - Thread-local context tracking
   - Event and status handling

7. **AsyncTracer Class** [Lines: 206-246]
   - Async-aware tracing implementation
   - Task-local context management
   - Async context manager support
   - Task cleanup handling

### Key Features

1. **Distributed Tracing** [Lines: 23-28]

   - Unique trace and span IDs
   - Parent-child relationship tracking
   - Baggage propagation
   - Sampling decisions

2. **Thread Safety** [Lines: 65-67]

   - Lock-based synchronization
   - Thread-local storage
   - Safe span processing
   - Concurrent access handling

3. **Sampling Control** [Lines: 51-60]

   - Configurable sampling rates
   - Consistent sampling decisions
   - Trace ID-based sampling
   - Performance optimization

4. **Context Management** [Lines: 168-181]
   - Context manager support
   - Automatic span lifecycle
   - Resource cleanup
   - Error handling

## Dependencies

### Required Packages

- `enum`: Enumeration support [Lines: 1]
- `typing`: Type hints [Lines: 2]
- `datetime`: Timestamp handling [Lines: 3]
- `uuid`: Unique ID generation [Lines: 4]
- `logging`: Log management [Lines: 5]
- `json`: Data serialization [Lines: 6]
- `asyncio`: Async support [Lines: 7]
- `dataclasses`: Data structure [Lines: 8]
- `contextlib`: Context management [Lines: 9]
- `threading`: Concurrency support [Lines: 10]
- `collections`: Data structures [Lines: 11]

### Internal Modules

None - Self-contained tracing module

## Known Issues

1. **Task Cleanup** [Lines: 241-245]
   - Task-local storage cleanup
   - Potential memory leaks
   - Manual cleanup required

## Performance Considerations

1. **Sampling Impact** [Lines: 51-60]

   - Configurable sampling rates
   - Performance vs data collection trade-off
   - Efficient sampling decisions

2. **Thread Safety** [Lines: 65-67]

   - Lock contention potential
   - Thread-local storage overhead
   - Synchronization costs

3. **Memory Usage** [Lines: 66]
   - Span storage growth
   - In-memory trace retention
   - Cleanup considerations

## Security Considerations

1. **Data Protection** [Lines: 27]

   - Baggage data isolation
   - Context separation
   - Thread isolation

2. **Trace Data** [Lines: 85-110]
   - Sensitive data in traces
   - Export format security
   - Data sanitization needs

## Trade-offs and Design Decisions

1. **Sampling Strategy**

   - **Decision**: Probabilistic sampling [Lines: 51-60]
   - **Rationale**: Balance between data collection and performance
   - **Trade-off**: Data completeness vs system overhead

2. **Storage Architecture**

   - **Decision**: In-memory span storage [Lines: 66]
   - **Rationale**: Fast access and processing
   - **Trade-off**: Memory usage vs persistence

3. **Context Management**

   - **Decision**: Thread/Task-local storage [Lines: 119, 211]
   - **Rationale**: Clean context isolation
   - **Trade-off**: Memory overhead vs context safety

4. **Async Support**
   - **Decision**: Separate async implementation [Lines: 206-246]
   - **Rationale**: Proper async context handling
   - **Trade-off**: Code duplication vs correctness
