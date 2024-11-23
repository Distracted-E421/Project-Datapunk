# D3 TypeScript Integration Guide

## Purpose
This guide outlines best practices for using D3.js with TypeScript in our Svelte components.

## Type Definitions

### Basic D3 Types
```typescript
// Selection types
type D3Selection<GElement extends BaseType = BaseType> = 
    Selection<GElement, unknown, HTMLElement, any>;

// Scale types
type TimeScale = ScaleTime<number, number>;
type LinearScale = ScaleLinear<number, number>;

// Data types
interface ChartDatum {
    timestamp: Date | string;
    value: number;
    [key: string]: any;
}
```

### Type Guards
Use type guards to ensure D3 objects are properly typed:

```typescript
function isD3Selection(value: unknown): value is D3Selection {
    return value !== null && 
           typeof value === 'object' && 
           'select' in value &&
           'selectAll' in value;
}

function isTimeScale(value: unknown): value is TimeScale {
    return value !== null && 
           typeof value === 'object' && 
           'domain' in value &&
           'range' in value &&
           'invert' in value;
}
```

## Best Practices

1. **Type Annotations**
   - Always specify generic types for D3 selections
   - Use type guards before operations
   - Define interfaces for data structures

2. **Error Handling**
   - Wrap D3 operations in try/catch blocks
   - Use error boundaries for chart components
   - Provide fallback UI for failed renders

3. **Component Structure**
   - Keep D3 logic separate from component logic
   - Use typed event handlers
   - Properly clean up selections on destroy

## Examples

### Basic Chart Component
```typescript
<script lang="ts">
    import type { D3Selection } from '$lib/types/d3';
    import { onMount, onDestroy } from 'svelte';
    
    let chart: D3Selection<SVGSVGElement>;
    
    onMount(() => {
        try {
            chart = d3.select('#chart')
                     .append('svg')
                     .attr('width', width)
                     .attr('height', height);
        } catch (error) {
            handleD3Error(error);
        }
    });
    
    onDestroy(() => {
        if (isD3Selection(chart)) {
            chart.remove();
        }
    });
</script>
```

### Data Updates
```typescript
function updateChart(data: ChartDatum[]) {
    if (!isD3Selection(chart)) return;
    
    try {
        const scale = d3.scaleTime()
            .domain(d3.extent(data, d => new Date(d.timestamp)))
            .range([0, width]);
            
        if (!isTimeScale(scale)) {
            throw new Error('Failed to create time scale');
        }
        
        // Chart update logic...
    } catch (error) {
        handleD3Error(error);
    }
}
``` 