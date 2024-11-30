# Mermaid Diagram Styling System

## Overview

This directory contains a modular CSS styling system for Mermaid.js diagrams, designed to create visually consistent and aesthetically pleasing architectural diagrams. The system uses a combination of CSS variables, custom shapes, gradients, and animations to represent different components of the system architecture.

## Style Modules

### Base Styles (`base.css`)

- **Color Palette**: Defines the core colors for different service types (frontend, gateway, services, etc.)
- **Depth System**: Implements an 8-level depth system for nested components
  - Gradually increasing opacity (0.2 to 0.65)
  - Matching stroke weights for visual hierarchy
  - Used for representing system layers and component nesting

### Components (`components.css`)

- **Basic Shapes**: Custom shapes for different node types:
  - Diamond (♦): For decision points
  - Hexagon (⬡): For load balancers
  - Cylinder (🛢): For databases
  - Cloud (☁): For external services
- **Specialized Components**:
  - Load Balancers: Hexagonal shape with centered design
  - Gateways: Trapezoidal shape for entry points
  - Databases: Rounded top with bottom indicator
  - Queues: Asymmetrical rounded design
  - Cache: Modified hexagonal shape

### Gradients (`gradients.css`)

- **Layer Gradients**: Color-coded gradients for different architectural layers
  - External Layer: Red tones
  - Gateway Layer: Blue tones
  - Core Layer: Green tones
  - Infrastructure Layer: Purple tones
- **Depth Variations**: Each layer has three gradient levels (L1-L3)
- **Overlay Effects**: Subtle gradient overlays for depth perception

### Patterns (`patterns.css`)

- **Background Textures**:
  - Grid: For top-level clusters
  - Dots: For nested clusters
  - Diagonal: For special components
- **SVG-based**: Lightweight, scalable pattern definitions
- **Opacity Control**: Subtle patterns (5% opacity) for visual interest

### Text Styling (`text.css`)

- **Typography**: Custom PixelOperator font for technical aesthetics
- **Contrast Management**: Dynamic text color adjustment
- **Enhanced Readability**:
  - Text shadows for contrast
  - Stroke effects for visibility
  - Size hierarchy for cluster labels

### Animations (`animations.css`)

- **Interactive States**:
  - Pulse: For active components
  - Glow: For highlighted elements
- **Performance**: Optimized animations for smooth rendering
- **Purpose**: Visual feedback for state changes

### Edge Styling (`edges.css`)

- **Connection Types**:
  - Bidirectional arrows
  - Dashed lines for async connections
  - Dotted lines for optional connections
- **Labels**: Semi-transparent backgrounds for readability

### Status Indicators (`status.css`)

- **State Visualization**:
  - Active: Green glow
  - Warning: Amber pulse
  - Error: Red highlight
- **Position**: Top-right corner of components
- **Visual Feedback**: Immediate state recognition

## Usage

### Theme Configuration

The system integrates with Mermaid's theming through `mermaid-theme.json`:

```json
{
  "theme": "dark",
  "themeVariables": {
    "darkMode": true,
    "background": "transparent",
    "primaryColor": "#1c1c2420",
    "secondaryColor": "#14141920",
    "tertiaryColor": "#25252520",
    "primaryTextColor": "#ffffff",
    "fontFamily": "PixelOperator, monospace"
  }
}
```

### Class Application

Apply styles in Mermaid diagrams using class definitions:

```mermaid
classDef frontend fill:var(--frontend-color)
classDef gateway fill:var(--gateway-color)
classDef service fill:var(--service-color)
```

### Depth Examples

```mermaid
subgraph cluster_0["External Layer"]
  subgraph cluster_1["Gateway Layer"]
    subgraph cluster_2["Core Services"]
      // Components inherit depth styling automatically
    end
  end
end
```

## Best Practices

1. **Consistency**: Use predefined colors and shapes for component types
2. **Hierarchy**: Leverage depth system for nested components
3. **Clarity**: Apply animations sparingly for important state changes
4. **Performance**: Use lightweight patterns and optimize animations
5. **Accessibility**: Ensure sufficient contrast for text elements

## File Structure

```text
config/
├── styles/
│   ├── index.css      # Main entry point
│   ├── base.css       # Core variables
│   ├── components.css # Shape definitions
│   ├── gradients.css  # Color gradients
│   ├── patterns.css   # Background patterns
│   ├── text.css      # Typography
│   ├── animations.css # State changes
│   ├── edges.css     # Connections
│   └── status.css    # State indicators
├── mermaid-theme.json # Theme configuration
└── README.md         # This documentation
```

This styling system creates a cohesive visual language for architectural diagrams while maintaining flexibility and performance. The modular approach allows for easy maintenance and extension of styles.
