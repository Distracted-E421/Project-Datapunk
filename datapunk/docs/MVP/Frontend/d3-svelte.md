# D3 Integration with Svelte

## Purpose
This guide outlines best practices for integrating D3.js with Svelte components, focusing on type safety and error handling.

## Type Safety

### Component Setup
```typescript
// Import types and guards
import type { D3Selection } from '$lib/utils/d3-guards';
import { 
    isD3Selection,
    validateD3Selection,
    validateScaleTime,
    validateScaleLinear,
    handleD3Error 
} from '$lib/utils/d3-guards';

// Declare typed variables
let svg: D3Selection<SVGSVGElement>;
let tooltip: D3Selection<HTMLDivElement>;
```

### Type Guards
Use type guards to ensure D3 objects are valid:

```typescript
// Check if selection exists
if (isD3Selection(svg)) {
    svg.remove();
}

// Validate selection before use
validateD3Selection(svg, 'ComponentName.methodName');

// Validate scales
validateScaleTime(xScale, 'ComponentName.methodName');
validateScaleLinear(yScale, 'ComponentName.methodName');
```

## Error Handling

### Try-Catch Blocks
Wrap D3 operations in try-catch blocks:

```typescript
function updateChart() {
    try {
        // D3 operations...
    } catch (error) {
        throw handleD3Error(error, 'ComponentName.updateChart');
    }
}
```

### Component Cleanup
Always clean up D3 selections on component destruction:

```typescript
onDestroy(() => {
    if (isD3Selection(svg)) {
        svg.remove();
    }
    if (isD3Selection(tooltip)) {
        tooltip.remove();
    }
});
```

## Best Practices

1. **Type Safety**
   - Use TypeScript with D3
   - Import specific types from d3-guards
   - Validate selections and scales before use

2. **Error Handling**
   - Wrap D3 operations in try-catch
   - Use handleD3Error for consistent error handling
   - Clean up resources on component destruction

3. **Performance**
   - Use reactive statements wisely
   - Avoid unnecessary redraws
   - Clean up old elements before updates

4. **Accessibility**
   - Add ARIA labels to charts
   - Include tooltips for data points
   - Provide alternative text representations

## Example Components

1. TimeSeriesChart
2. GaugeChart
3. BarChart
4. PieChart

## Testing

1. Unit Tests
```typescript
import { render } from '@testing-library/svelte';
import TimeSeriesChart from './TimeSeriesChart.svelte';

test('renders without data', () => {
    const { container } = render(TimeSeriesChart, { props: { data: [] }});
    expect(container.querySelector('.no-data')).toBeInTheDocument();
});

test('renders with data', () => {
    const data = [
        { timestamp: '2024-01-01', value: 10 },
        { timestamp: '2024-01-02', value: 20 }
    ];
    const { container } = render(TimeSeriesChart, { props: { data }});
    expect(container.querySelector('.line')).toBeInTheDocument();
});
```

2. Integration Tests
```typescript
test('updates on data change', async () => {
    const { component, container } = render(TimeSeriesChart);
    await component.$set({ data: newData });
    expect(container.querySelectorAll('.point').length).toBe(newData.length);
});
```

## Resources

1. [D3.js Documentation](https://d3js.org/)
2. [Svelte Documentation](https://svelte.dev/)
3. [TypeScript Documentation](https://www.typescriptlang.org/) 