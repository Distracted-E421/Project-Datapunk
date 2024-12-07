# Cluster Rebalancer Documentation

## Purpose

Manages the redistribution of cache keys across cluster nodes to maintain balanced data distribution. Implements multiple rebalancing strategies to handle different operational requirements while preserving data consistency and TTL values.

## Implementation

### Core Components

1. **RebalanceStrategy** [Lines: 8-19]

   - Enumeration of available rebalancing strategies
   - GRADUAL: Minimizes performance impact
   - IMMEDIATE: Fastest rebalancing
   - OFF_PEAK: Operates during low-traffic hours

2. **ClusterRebalancer** [Lines: 21-207]
   - Manages key redistribution process
   - Supports multiple rebalancing strategies
   - Handles interruption and failure cases
   - Preserves data consistency and TTL values

### Key Features

1. **Strategy Selection** [Lines: 63-73]

   - Dynamic strategy selection
   - Strategy-specific implementation
   - Configurable behavior
   - Interruptible operation

2. **Key Identification** [Lines: 85-119]

   - Memory-efficient key scanning
   - Namespace-aware key filtering
   - Target node determination
   - Duplicate key handling

3. **Rebalancing Methods** [Lines: 120-207]
   - Immediate bulk transfer
   - Gradual batch processing
   - Off-peak execution window
   - Error handling and recovery

## Dependencies

### Required Packages

- asyncio: Async operation support [Lines: 3]
- datetime: Time-based operations [Lines: 5]

### Internal Modules

- cluster_manager: ClusterNode and ClusterManager types [Lines: 7]

## Known Issues

1. **Key Duplication** [Lines: 161-162]

   - Temporary key duplication during transfer
   - Potential consistency issues
   - TODO: Add metrics for monitoring

2. **Failed Transfers** [Lines: 127-128]

   - No retry logic for failed transfers
   - FIXME: Implement retry mechanism
   - Error logging only

3. **Key Scanning** [Lines: 94-95]
   - Possible key duplicates during scan
   - TODO: Handle duplicate keys
   - No deduplication mechanism

## Performance Considerations

1. **Immediate Rebalancing** [Lines: 120-149]

   - Uses pipelining for efficiency
   - High system load during operation
   - Potential impact on node performance
   - No rate limiting

2. **Gradual Rebalancing** [Lines: 150-190]

   - Controlled batch sizes
   - Configurable sleep intervals
   - Minimal performance impact
   - Longer completion time

3. **Off-Peak Rebalancing** [Lines: 191-207]
   - Time-window restricted operation
   - Hardcoded window (2 AM - 5 AM)
   - Sleep during peak hours
   - TODO: Configurable window

## Security Considerations

1. **Data Transfer** [Lines: 138-146]

   - Plain data transfer between nodes
   - No encryption in transit
   - Relies on network security

2. **Access Control** [Lines: 85-119]
   - No explicit authentication
   - Assumes trusted cluster
   - Internal network operation

## Trade-offs and Design Decisions

1. **Rebalancing Strategies**

   - **Decision**: Multiple strategy support [Lines: 8-19]
   - **Rationale**: Different operational needs
   - **Trade-off**: Complexity vs flexibility

2. **Key Transfer**

   - **Decision**: Copy-then-delete approach [Lines: 143-146]
   - **Rationale**: Prevents data loss
   - **Trade-off**: Temporary duplication vs safety

3. **Scanning Method**
   - **Decision**: Redis SCAN command [Lines: 104-108]
   - **Rationale**: Memory efficiency
   - **Trade-off**: Possible duplicates vs memory usage

## Future Improvements

1. **Transfer Reliability** [Lines: 127-128]

   - Implement retry logic
   - Add failure recovery
   - Track transfer success rates

2. **Monitoring** [Lines: 161-162]

   - Add metrics collection
   - Track rebalancing progress
   - Monitor node load

3. **Configuration** [Lines: 198-199]

   - Make off-peak window configurable
   - Add rate limiting options
   - Support partial rebalancing

4. **Key Handling** [Lines: 94-95]
   - Implement duplicate key handling
   - Add key verification
   - Support selective rebalancing
