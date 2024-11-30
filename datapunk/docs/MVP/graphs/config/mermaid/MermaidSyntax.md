# Advanced Mermaid Syntax Guide

## Purpose

This document provides a comprehensive reference for all Mermaid diagram syntaxes, including advanced features and configurations.

## Context

Mermaid supports multiple diagram types, each with its own syntax rules and capabilities.([1](https://github.com/mermaid-js/mermaid/tree/develop/packages/mermaid/src/docs/syntax))

## Detailed Syntax Reference

### 1. Flowchart Syntax

```mermaid
graph TD
    %% Basic node types
    A[Square Node]
    B(Rounded Node)
    C([Stadium Node])
    D[[Subroutine]]
    E[(Database)]
    F((Circle))
    G>Asymmetric]
    H{Diamond}
    I{{Hexagon}}
    J[/Parallelogram/]
    K[\Parallelogram alt\]
    L[/Trapezoid\]
    M[\Trapezoid alt/]

    %% Connection types
    A --> B %% Arrow
    B --- C %% Line
    C -.-> D %% Dotted arrow
    D ==> E %% Thick arrow
    E -.- F %% Dotted line
    F ==== G %% Thick line

    %% Advanced connections
    H --text--> I
    I ==text==> J
    J -.text.-> K
    K --text--- L
    L ==text=== M
```

### 2. Sequence Diagram Syntax

```mermaid
sequenceDiagram
    %% Participant definitions
    participant A as Alice
    participant B as Bob
    actor U as User

    %% Message types
    A->>B: Solid arrow
    B-->>A: Dotted arrow
    A-xB: Cross end
    B--xA: Dotted cross
    A--)B: Open arrow
    B--)A: Open arrow

    %% Activations
    activate A
    A->>+B: Activate target
    B->>-A: Deactivate target
    deactivate A

    %% Notes
    Note left of A: Left note
    Note right of B: Right note
    Note over A,B: Spanning note

    %% Loops and alternatives
    loop Every minute
        A->>B: Heartbeat
    end

    alt Success case
        A->>B: Success
    else Error case
        A->>B: Error
    end

    %% Optional paths
    opt Optional step
        A->>B: Optional message
    end
```

### 3. Class Diagram Syntax

```mermaid
classDiagram
    %% Class definitions
    class Animal {
        +String name
        +int age
        +makeSound() void
        -private_method() bool
        #protected_method() void
    }

    %% Inheritance
    Animal <|-- Dog
    Animal <|-- Cat

    %% Composition
    Dog *-- Tail

    %% Aggregation
    Pack o-- Dog

    %% Relationships
    Dog --> Food
    Cat ..> Mouse

    %% Generic types
    class List~T~ {
        +add(T item) void
        +get(int index) T
    }
```

### 4. Entity Relationship Diagram Syntax

```mermaid
erDiagram
    %% Entity definitions with attributes
    CUSTOMER {
        string id PK
        string name
        int age
    }

    ORDER {
        int id PK
        string status
        date created_at
    }

    %% Relationships and cardinality
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE_ITEM : contains
    PRODUCT ||--o{ LINE_ITEM : "ordered in"
```

### 5. State Diagram Syntax

```mermaid
stateDiagram-v2
    %% States
    [*] --> Still
    Still --> Moving
    Moving --> Still
    Moving --> Crash
    Crash --> [*]

    %% Composite states
    state Moving {
        Slow --> Fast
        Fast --> Slow

        %% Parallel states
        state "Moving Details" as MovingDetails {
            [*] --> Accelerating
            Accelerating --> Cruising
            Cruising --> Decelerating
        }
    }
```

### 6. Gantt Chart Syntax

```mermaid
gantt
    %% Project settings
    title Project Timeline
    dateFormat YYYY-MM-DD
    axisFormat %d/%m

    %% Sections and tasks
    section Planning
    Research        :a1, 2024-01-01, 7d
    Documentation   :after a1, 5d

    section Development
    Coding         :crit, 2024-01-15, 14d
    Testing        :2024-02-01, 7d

    %% Milestones
    section Milestones
    Release v1.0   :milestone, 2024-02-15, 0d
```

### 7. Pie Chart Syntax

```mermaid
pie
    title Distribution
    "A" : 45.5
    "B" : 30.2
    "C" : 24.3
```

### 8. Git Graph Syntax

```mermaid
gitGraph
    commit
    branch develop
    checkout develop
    commit
    commit
    checkout main
    merge develop
    commit
    branch feature
    checkout feature
    commit
    checkout develop
    merge feature
    checkout main
    merge develop
```

## Advanced Features

### Theme Configuration

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#ff0000',
    'primaryTextColor': '#fff',
    'primaryBorderColor': '#fff',
    'lineColor': '#f00',
    'secondaryColor': '#006100',
    'tertiaryColor': '#fff'
  }
}}%%
```

### Directives

```mermaid
%%{init: {'securityLevel': 'loose', 'theme':'dark'}}%%
%%{config: { 'fontFamily': 'arial', 'fontSize': 14 } }%%
```

## Error Handling and Logging

- Syntax validation through live editor
- Browser console error messages
- Common error patterns and solutions

## Known Issues

- Complex diagrams may have performance impact
- Browser compatibility considerations
- Mobile rendering limitations

## Performance Considerations

- Limit node count for complex diagrams
- Use appropriate diagram type for data representation
- Consider lazy loading for multiple diagrams

## Security Considerations

- Sanitize user input for dynamic diagrams
- Use appropriate security level settings
- Validate external data sources

## Testing Notes

- Verify rendering in multiple browsers
- Test different themes and configurations
- Validate complex diagram structures

## References

1. [Mermaid Syntax Documentation](https://github.com/mermaid-js/mermaid/tree/develop/packages/mermaid/src/docs/syntax)
2. [Mermaid Configuration Guide](https://github.com/mermaid-js/mermaid/tree/develop/packages/mermaid/src/docs/config)
3. [Community Examples](https://github.com/mermaid-js/mermaid/tree/develop/packages/mermaid/src/docs/community)
