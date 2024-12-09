# Query Federation Splitter Module

## Purpose

This module is responsible for splitting complex federated queries into optimized subqueries that can be executed across different data sources. It analyzes query dependencies, identifies push-down operations, and creates an efficient execution plan that balances load across data sources.

## Implementation

### Core Components

1. **SubQuery** [Lines: 6-13]

   - Represents split query parts
   - Tracks source assignments
   - Manages dependencies
   - Estimates execution costs

2. **QuerySplitter** [Lines: 15-354]
   - Main splitting logic
   - Source capability tracking
   - Query optimization
   - Load balancing

### Key Features

1. **Query Analysis** [Lines: 32-80]

   - Dependency analysis
   - Push-down identification
   - Source capability matching
   - Cost estimation

2. **Query Splitting** [Lines: 81-150]

   - Table-based splitting
   - Operation-based splitting
   - Dependency preservation
   - Source assignment

3. **Optimization** [Lines: 151-250]

   - Subquery merging
   - Load balancing
   - Cost-based decisions
   - Capability matching

4. **Load Management** [Lines: 251-354]
   - Load distribution
   - Query movement
   - Source rebalancing
   - Capability verification

## Dependencies

### Required Packages

- typing: Type hints
- dataclasses: Data structure definitions
- ..parser.core: Query parsing components
- .query_fed_core: Federation core functionality

### Internal Dependencies

- QueryPlan: Query plan representation
- QueryNode: Query node structure
- DataSourceStats: Source statistics
- Source capabilities tracking

## Known Issues

1. **Query Splitting** [Lines: 32-80]

   - Basic dependency analysis
   - Limited complex query handling
   - Simple cost estimation

2. **Load Balancing** [Lines: 251-354]

   - Fixed thresholds
   - Basic rebalancing strategy
   - Limited cross-source optimization

3. **Query Movement** [Lines: 300-354]
   - Simple capability checking
   - Basic movement criteria
   - Limited optimization scope

## Performance Considerations

1. **Query Analysis**

   - Dependency analysis overhead
   - Push-down identification cost
   - Source capability matching impact
   - Cost estimation accuracy

2. **Resource Usage**
   - Memory for query plans
   - CPU for optimization
   - Network for query movement
   - Storage for intermediate results

## Security Considerations

1. **Data Access**

   - No explicit security checks
   - Assumes secure sources
   - Basic access patterns
   - Limited validation

2. **Resource Protection**
   - Basic load limits
   - Simple thresholds
   - Minimal validation
   - No explicit quotas

## Trade-offs and Design Decisions

1. **Splitting Strategy**

   - **Decision**: Table-based splitting [Lines: 81-150]
   - **Rationale**: Natural data boundaries
   - **Trade-off**: Potential suboptimal splits

2. **Load Balancing**

   - **Decision**: Cost-based movement [Lines: 251-354]
   - **Rationale**: Even resource utilization
   - **Trade-off**: Movement overhead

3. **Capability Matching**
   - **Decision**: Strict capability checking [Lines: 300-354]
   - **Rationale**: Ensure query executability
   - **Trade-off**: Limited flexibility

## Future Improvements

1. **Enhanced Analysis**

   - Advanced dependency tracking
   - Complex query optimization
   - Dynamic cost modeling
   - Improved capability matching

2. **Advanced Load Balancing**

   - Dynamic thresholds
   - Predictive rebalancing
   - Cross-source optimization
   - Resource monitoring

3. **Query Movement**
   - Sophisticated movement criteria
   - Cost-benefit analysis
   - Partial query movement
   - State preservation
