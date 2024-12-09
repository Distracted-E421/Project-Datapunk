# Query Federation Planner

## Purpose

The planner module is responsible for planning and optimizing distributed query execution across federated data sources. It handles query decomposition, source selection, and optimization of distributed query plans. The module is a critical component in the federation layer that enables efficient execution of queries across heterogeneous data sources.

## Implementation

### Core Components

1. **DataSourceType (Enum)**

   - Defines supported types of data sources in the federation:
     - RELATIONAL
     - DOCUMENT
     - GRAPH
     - OBJECT_STORE
     - TIME_SERIES

2. **DataSource (Dataclass)**

   - Represents a federated data source with:
     - name: Unique identifier
     - type: DataSourceType
     - capabilities: Set of supported operations
     - cost_factors: Operation cost weights
     - statistics: Source-specific statistics

3. **SubQuery (Dataclass)**

   - Represents a portion of a query to be executed on a specific source:
     - source: Target DataSource
     - query: QueryNode containing the query fragment
     - estimated_cost: Execution cost estimate
     - dependencies: List of dependent SubQueries
     - result_size: Estimated result size

4. **DistributedQueryPlanner (Class)**
   - Main planner class implementing the distributed query planning logic
   - Key methods:
     - register_data_source(): Registers data sources and their optimizers
     - plan_query(): Creates optimized distributed query plans
     - \_analyze_requirements(): Determines required capabilities
     - \_find_capable_sources(): Identifies capable data sources
     - \_split_query(): Decomposes queries into sub-queries
     - \_optimize_sub_queries(): Optimizes individual sub-queries
     - \_create_execution_plan(): Creates the final execution plan

### Query Planning Process

1. **Requirement Analysis**

   - Analyzes query to determine required capabilities
   - Handles SELECT queries with various operations (joins, grouping, ordering)
   - Identifies special requirements (text search, geospatial)

2. **Source Selection**

   - Finds data sources capable of handling query requirements
   - Matches required capabilities against source capabilities
   - Filters sources based on capability subsets

3. **Query Decomposition**

   - Splits queries based on table locations
   - Groups tables by data source
   - Creates sub-queries for each source group
   - Maintains dependencies between sub-queries

4. **Optimization**

   - Applies source-specific optimizers to sub-queries
   - Estimates execution costs
   - Performs cost-based optimization
   - Creates optimal execution plans

5. **Plan Creation**
   - Sorts sub-queries based on dependencies
   - Identifies optimization opportunities
   - Handles parallel execution, push-down optimizations
   - Considers data locality and common sub-expressions

## Dependencies

- parser.core.QueryNode: Base query representation
- parser.core.QueryType: Query type enumeration
- optimizer.index_aware.IndexAwareOptimizer: Source-specific query optimization

## Known Issues

1. Placeholder implementations for:
   - \_find_table_source(): Needs metadata catalog integration
   - \_filter_query_for_tables(): Requires complete query filtering logic
   - \_topological_sort(): Needs full topological sorting implementation

## Performance Considerations

1. Cost Estimation

   - Considers operation costs and data size
   - Scales cost based on data volume (1M record units)
   - Uses source-specific cost factors

2. Optimization Strategies
   - Parallel execution opportunities
   - Push-down optimizations
   - Common sub-expression elimination
   - Data locality optimizations

## Security Considerations

1. Source Registration

   - Requires secure source registration process
   - Should validate source capabilities
   - Must protect source statistics and metadata

2. Query Decomposition
   - Must maintain security constraints across sub-queries
   - Should consider source-specific access controls
   - Needs to handle sensitive data appropriately

## Trade-offs and Design Decisions

1. **Query Splitting Strategy**

   - Current approach splits by table location
   - Pros:
     - Simple and efficient implementation
     - Clear source boundaries
   - Cons:
     - May not be optimal for all query patterns
     - Could miss cross-source optimization opportunities

2. **Cost Model**

   - Simple multiplicative cost model
   - Pros:
     - Easy to understand and maintain
     - Quick to compute
   - Cons:
     - May not capture complex operation interactions
     - Could oversimplify some cost factors

3. **Optimization Approach**

   - Two-phase optimization (local then global)
   - Pros:
     - Leverages source-specific optimizers
     - Maintains source autonomy
   - Cons:
     - May miss global optimization opportunities
     - Could lead to suboptimal plans in some cases

4. **Dependency Management**
   - Simple dependency tracking
   - Pros:
     - Clear execution ordering
     - Easy to implement
   - Cons:
     - May not handle complex dependencies optimally
     - Could limit parallelization opportunities
