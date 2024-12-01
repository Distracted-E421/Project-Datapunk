# Mermaid Diagram Layout Standards

## Core Layout Principles

### 1. Shape Control

- Target a roughly square aspect ratio (1:1 to 1:1.5)
- Maximum width should not exceed 1.5x height
- Use vertical layouts (`TB`) as the default direction
- Break wide diagrams into vertical sections using subgraphs

### 2. Configuration and Initialization

```javascript
mermaid.initialize({
  startOnLoad: true,
  theme: "forest",
  sequence: {
    diagramMarginX: 50,
    diagramMarginY: 10,
    actorMargin: 50,
    width: 150,
    height: 65,
    boxMargin: 10,
    boxTextMargin: 5,
    messageMargin: 35,
    mirrorActors: true,
  },
  flowchart: {
    htmlLabels: false,
    curve: "linear",
  },
});
```

### 3. Development Integration

#### Editor Integration

- Use Mermaid plugins with:
  - Visual Studio Code
  - Atom
  - Sublime Text
  - Benefits: Syntax highlighting, code completion, live preview

#### Documentation Platforms

- Direct integration with:
  - GitBook
  - MkDocs
  - Docusaurus
  - Markdown-based documentation

#### DevOps Integration

- Embed diagrams in:
  - CI/CD pipeline reports
  - Jenkins documentation
  - GitLab CI visualizations
  - Build process documentation

### 4. Advanced Layout Techniques

```mermaid
graph TB
    %% Define layout settings
    %%{
        init: {
            'flowchart': {
                'nodeSpacing': 50,
                'rankSpacing': 80,
                'curve': 'basis',
                'padding': 20
            }
        }
    }%%

    %% Demonstrate advanced grouping
    subgraph group1[Primary Flow]
        direction TB
        A[Start] --> B{Decision}
        B -->|Yes| C[Process]
        B -->|No| D[Alternative]
    end

    subgraph group2[Secondary Flow]
        direction TB
        E[Input] --> F((Process))
        F -.->|Async| G[Output]
    end

    %% Cross-group connections
    C --> F
    D -.-> G
```

### 5. Visual Enhancement Techniques

#### Node Styling

- Use diverse shapes for clear visual hierarchy:
  - `[Rectangle]` - Standard processes
  - `(Round)` - Entry/Exit points
  - `{Diamond}` - Decision points
  - `((Circle))` - Interface points
  - `>Asymmetric]` - Inputs/Outputs

#### Connection Types

```mermaid
graph TB
    A[Start] --> B[Process]
    B -.->|Async| C[Result]
    C ===>|Critical| D[End]
    D -->|Optional| E[Cleanup]
```

### 6. Complex Flow Management

#### Using Alt Sections

```mermaid
sequenceDiagram
    participant User
    participant System

    alt Valid Input
        User->>System: Submit Data
        System-->>User: Success
    else Invalid Input
        User->>System: Submit Data
        System-->>User: Error
    end
```

#### Loop Visualization

```mermaid
sequenceDiagram
    participant Process
    participant Worker

    loop Until Complete
        Process->>Worker: Process Item
        Worker-->>Process: Result
    end
```

### 7. Interactive Enhancements

#### HTML Integration

```mermaid
graph TB
    A[Process] -->|"<a href='#details'>Click for Details</a>"| B
    B -->|"<div class='custom-style'>Interactive Node</div>"| C
```

#### Dynamic Elements

- Include clickable elements
- Add HTML labels for rich formatting
- Embed links to documentation
- Use hover states for additional information

## Implementation Guidelines

### 1. CSS Configuration

```css
.mermaid {
  --diagram-padding: 20px;
  --node-spacing: 50px;
  --rank-spacing: 80px;

  display: flex;
  justify-content: center;
  padding: var(--diagram-padding);
  max-width: min(900px, 90vw);
  aspect-ratio: 1 / 1.2;
}
```

### 2. Best Practices

1. **Vertical Flow Organization**

   - Stack related components vertically
   - Use subgraphs for parallel processes
   - Limit horizontal node spread to 3-4 items

2. **Connection Management**

   - Use different line styles meaningfully:
     - Solid (`-->`) for main flow
     - Dotted (`-.->`) for async/optional
     - Thick (`==>`) for critical paths
   - Minimize crossing lines with proper node placement

3. **Interactive Elements**
   - Use notes for additional context
   - Implement loops for repetitive processes
   - Utilize alt sections for conditional flows

### 3. Troubleshooting

| Common Issues     | Solution                                           |
| ----------------- | -------------------------------------------------- |
| Wide diagrams     | Split into vertical subgraphs                      |
| Dense connections | Use intermediate nodes                             |
| Overlapping       | Increase spacing variables                         |
| Poor readability  | Implement proper node shapes and connection styles |

## Advanced Examples

### Complex System Architecture

```mermaid
graph TB
    subgraph external[Client Layer]
        direction TB
        A[Web Client]
        B[Mobile Client]
    end

    subgraph gateway[Gateway Layer]
        direction TB
        C{Load Balancer}
        D((API Gateway))
    end

    subgraph services[Service Layer]
        direction TB
        E[(Database)]
        F[Service 1]
        G[Service 2]
    end

    A & B --> C
    C --> D
    D --> F & G
    F & G --> E
```

## Export Options

### Format Support

- SVG (recommended for web)
- mmd (recommended for source control and design)

## Maintenance Guidelines

1. **Version Control**

   - Store diagrams as both mmd and svg in source control
   - Review diagram changes in PRs
   - Maintain diagram history

2. **Documentation Sync**

   - Keep diagrams updated with code changes
   - Include diagrams in code review process
   - Use of comments should be liberal

3. **Performance Optimization**
   - Use lazy loading for multiple diagrams
   - Implement caching strategies
