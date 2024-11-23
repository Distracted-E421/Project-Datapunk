<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import * as d3 from 'd3';
    import type { ChartData } from '$lib/types/charts';
    import type { Selection, Line, Axis } from '$lib/types/d3';
    import { 
        isD3Selection,
        validateD3Selection,
        validateScaleTime,
        validateScaleLinear,
        handleD3Error 
    } from '$lib/utils/d3-guards';
    
    export let data: ChartData[] = [];
    export let yLabel = '';
    export let color = '#3B82F6';
    export let xKey = 'timestamp';
    export let yKey = 'value';
    export let title = '';
    
    let chartDiv: HTMLDivElement;
    let svg: Selection<SVGGElement, unknown, HTMLElement, any>;
    let tooltip: Selection<HTMLDivElement, unknown, HTMLElement, any>;
    
    $: if (chartDiv && data) {
        updateChart();
    }
    
    onMount(() => {
        setupChart();
    });
    
    onDestroy(() => {
        if (isD3Selection(svg)) {
            svg.remove();
        }
        if (isD3Selection(tooltip)) {
            tooltip.remove();
        }
    });
    
    function setupChart() {
        try {
            // Clear previous chart
            d3.select(chartDiv).selectAll('*').remove();
            
            // Set up dimensions
            const margin = { top: 20, right: 20, bottom: 30, left: 50 };
            const width = chartDiv.clientWidth - margin.left - margin.right;
            const height = 400 - margin.top - margin.bottom;
            
            // Create SVG
            svg = d3.select(chartDiv)
                .append('svg')
                .attr('width', width + margin.left + margin.right)
                .attr('height', height + margin.top + margin.bottom)
                .append('g')
                .attr('transform', `translate(${margin.left},${margin.top})`);
                
            validateD3Selection(svg, 'TimeSeriesChart.setupChart');
            
            // Create tooltip
            tooltip = d3.select(chartDiv)
                .append('div')
                .attr('class', 'tooltip')
                .style('opacity', 0);
                
            validateD3Selection(tooltip, 'TimeSeriesChart.setupChart');
            
        } catch (error) {
            throw handleD3Error(error, 'TimeSeriesChart.setupChart');
        }
    }
    
    function updateChart() {
        if (!svg || !data.length) return;
        
        try {
            validateD3Selection(svg, 'TimeSeriesChart.updateChart');
            
            // Create scales
            const xScale = d3.scaleTime()
                .domain(d3.extent(data, d => new Date(d[xKey])) as [Date, Date])
                .range([0, chartDiv.clientWidth - 70]);
                
            validateScaleTime(xScale, 'TimeSeriesChart.updateChart');
            
            const yScale = d3.scaleLinear()
                .domain([0, d3.max(data, d => d[yKey]) || 0])
                .range([chartDiv.clientHeight - 50, 0]);
                
            validateScaleLinear(yScale, 'TimeSeriesChart.updateChart');
            
            // Create line generator
            const line = d3.line<ChartData>()
                .x(d => xScale(new Date(d[xKey])))
                .y(d => yScale(d[yKey]));
            
            // Update axes
            const xAxis = d3.axisBottom(xScale);
            const yAxis = d3.axisLeft(yScale);
            
            svg.select('.x-axis')
                .attr('transform', `translate(0,${chartDiv.clientHeight - 50})`)
                .call(xAxis);
                
            svg.select('.y-axis')
                .call(yAxis);
            
            // Update line
            const path = svg.selectAll('.line')
                .data([data]);
                
            path.enter()
                .append('path')
                .merge(path as any)
                .attr('class', 'line')
                .attr('d', line)
                .attr('fill', 'none')
                .attr('stroke', color)
                .attr('stroke-width', 2);
                
            // Update points
            const points = svg.selectAll('.point')
                .data(data);
                
            points.enter()
                .append('circle')
                .merge(points as any)
                .attr('class', 'point')
                .attr('cx', d => xScale(new Date(d[xKey])))
                .attr('cy', d => yScale(d[yKey]))
                .attr('r', 4)
                .attr('fill', color)
                .on('mouseover', (event: MouseEvent, d: ChartData) => {
                    tooltip.transition()
                        .duration(200)
                        .style('opacity', .9);
                    tooltip.html(
                        `${new Date(d[xKey]).toLocaleString()}<br/>${d[yKey]}`
                    )
                    .style('left', `${event.pageX + 10}px`)
                    .style('top', `${event.pageY - 28}px`);
                })
                .on('mouseout', () => {
                    tooltip.transition()
                        .duration(500)
                        .style('opacity', 0);
                });
                
            // Remove old elements
            path.exit().remove();
            points.exit().remove();
            
        } catch (error) {
            throw handleD3Error(error, 'TimeSeriesChart.updateChart');
        }
    }
</script>

<div class="chart-container" bind:this={chartDiv}>
    {#if !data.length}
        <div class="no-data">No data available</div>
    {/if}
</div>

<style>
    .chart-container {
        width: 100%;
        height: 400px;
        position: relative;
    }
    
    .no-data {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: #666;
        font-style: italic;
    }
    
    :global(.tooltip) {
        position: absolute;
        padding: 8px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        border-radius: 4px;
        pointer-events: none;
        font-size: 12px;
    }
</style> 