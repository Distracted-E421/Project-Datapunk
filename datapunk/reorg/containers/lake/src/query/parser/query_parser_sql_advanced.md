# Advanced SQL Query Parser Module

## Purpose

Extends the base SQL parser with advanced features including Common Table Expressions (CTEs), set operations, MERGE statements, window functions, and subquery support. Provides comprehensive parsing capabilities for complex SQL operations while maintaining integration with the core parser framework.

## Implementation

### Core Components

1. **Window Components** [Lines: 7-24]

   - Window frame types
   - Frame specifications
   - Window definitions
   - Frame bounds

2. **Advanced Parser** [Lines: 26-46]

   - Extended parser class
   - Feature detection
   - Query routing
   - Operation parsing

3. **Query Processing** [Lines: 47-306]
   - CTE handling
   - Set operations
   - MERGE statements
   - Window functions

### Key Features

1. **CTE Processing** [Lines: 47-65]

   - CTE definition parsing
   - Reference resolution
   - Subquery handling
   - Tree construction

2. **Set Operations** [Lines: 67-85]

   - UNION support
   - INTERSECT handling
   - EXCEPT processing
   - Plan generation

3. **MERGE Handling** [Lines: 87-110]

   - Target table processing
   - Source handling
   - Match conditions
   - Action processing

4. **Window Functions** [Lines: 111-131]
   - Function extraction
   - Window specification
   - Frame handling
   - Partition processing

### Advanced Features

1. **Subquery Support** [Lines: 132-148]

   - Scalar subqueries
   - EXISTS subqueries
   - Subquery parsing
   - Plan integration

2. **CTE Management** [Lines: 149-194]
   - Definition splitting
   - Reference tracking
   - Node replacement
   - Tree modification

## Dependencies

### Required Packages

- typing: Type hint support
- dataclasses: Data structure definitions
- enum: Enumeration support

### Internal Modules

- query_parser_core: Core components
- query_parser_sql: Base SQL parser

## Known Issues

1. **CTE Processing** [Lines: 149-194]

   - Basic reference handling
   - Limited recursion support
   - Simple tree modification

2. **Window Functions** [Lines: 251-290]
   - Basic frame support
   - Limited bound types
   - Simple expressions only

## Performance Considerations

1. **CTE Resolution** [Lines: 179-194]

   - Tree traversal overhead
   - Node replacement cost
   - Memory for references

2. **Query Splitting** [Lines: 149-171]
   - String manipulation cost
   - Memory for parts
   - Parsing overhead

## Security Considerations

1. **Input Validation** [Lines: 47-65]

   - Query validation
   - CTE verification
   - Reference checking

2. **Tree Modification** [Lines: 179-194]
   - Node validation
   - Reference safety
   - Tree integrity

## Trade-offs and Design Decisions

1. **Window Structure**

   - **Decision**: Separate frame types [Lines: 7-24]
   - **Rationale**: Clean type separation
   - **Trade-off**: Code clarity vs. complexity

2. **CTE Handling**

   - **Decision**: Reference resolution [Lines: 179-194]
   - **Rationale**: Clean tree modification
   - **Trade-off**: Performance vs. maintainability

3. **Parser Extension**
   - **Decision**: Feature detection [Lines: 26-46]
   - **Rationale**: Clean feature routing
   - **Trade-off**: Flexibility vs. overhead

## Future Improvements

1. **CTE Enhancement** [Lines: 149-194]

   - Add recursion support
   - Implement optimization
   - Support materialization

2. **Window Functions** [Lines: 251-290]

   - Add complex frames
   - Support more bounds
   - Implement optimization

3. **Query Features** [Lines: 47-110]
   - Add WITH RECURSIVE
   - Support LATERAL
   - Implement VALUES
