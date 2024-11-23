<script lang="ts">
    import { onMount } from 'svelte';
    import * as d3 from 'd3';
    import type { Selection, BaseType } from 'd3';
    
    interface Threshold {
        value: number;
        color: string;
    }
    
    interface ArcDatum {
        startAngle: number;
        endAngle: number;
    }
    
    export let value: number;
    export let min: number = 0;
    export let max: number = 100;
    export let title: string = '';
    export let units: string = '';
    export let thresholds: Threshold[] = [
        { value: 60, color: '#10B981' },  // Green
        { value: 80, color: '#F59E0B' },  // Yellow
        { value: 100, color: '#EF4444' }  // Red
    ];
    
    let chartDiv: HTMLDivElement;
    let svg: Selection<SVGGElement, unknown, HTMLElement, any>;
    
    $: if (chartDiv && typeof value === 'number') {
        drawGauge();
    }
    
    function drawGauge() {
        const width = chartDiv.clientWidth;
        const height = width;
        const radius = Math.min(width, height) / 2;
        
        // Clear previous content
        d3.select(chartDiv).selectAll('*').remove();
        
        svg = d3.select(chartDiv)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .append('g')
            .attr('transform', `translate(${width/2},${height/2})`);
            
        // Create scale
        const scale = d3.scaleLinear()
            .domain([min, max])
            .range([-Math.PI * 0.75, Math.PI * 0.75]);
            
        // Create arc generator
        const arc = d3.arc<ArcDatum>()
            .innerRadius(radius * 0.6)
            .outerRadius(radius * 0.8)
            .startAngle((d: ArcDatum) => d.startAngle)
            .endAngle((d: ArcDatum) => d.endAngle);
            
        // Add background arc
        const backgroundArc: ArcDatum = {
            startAngle: -Math.PI * 0.75,
            endAngle: Math.PI * 0.75
        };
        
        svg.append('path')
            .datum(backgroundArc)
            .style('fill', '#f3f4f6')
            .attr('d', arc);
            
        // Add colored arcs for thresholds
        let startAngle = -Math.PI * 0.75;
        thresholds.forEach((threshold) => {
            const endAngle = scale(threshold.value);
            
            const thresholdArc: ArcDatum = {
                startAngle: startAngle,
                endAngle: endAngle
            };
            
            svg.append('path')
                .datum(thresholdArc)
                .style('fill', threshold.color)
                .attr('d', arc);
                
            startAngle = endAngle;
        });
        
        // Add needle
        const needleLength = radius * 0.7;
        const needleRadius = radius * 0.02;
        
        const needle = svg.append('g')
            .attr('class', 'needle');
            
        needle.append('circle')
            .attr('cx', 0)
            .attr('cy', 0)
            .attr('r', needleRadius)
            .style('fill', '#374151');
            
        needle.append('path')
            .attr('d', `M ${-needleRadius} 0 L ${needleLength} 0 L ${-needleRadius} ${needleRadius} Z`)
            .style('fill', '#374151')
            .attr('transform', `rotate(${scale(value) * 180 / Math.PI})`);
            
        // Add value text
        svg.append('text')
            .attr('class', 'value')
            .attr('y', radius * 0.3)
            .attr('text-anchor', 'middle')
            .style('font-size', `${radius * 0.2}px`)
            .text(`${value}${units}`);
            
        // Add title
        if (title) {
            svg.append('text')
                .attr('class', 'title')
                .attr('y', -radius * 0.2)
                .attr('text-anchor', 'middle')
                .style('font-size', `${radius * 0.15}px`)
                .text(title);
        }
    }
</script>

<div class="gauge-container" bind:this={chartDiv}></div>

<style>
    .gauge-container {
        width: 100%;
        aspect-ratio: 1;
    }
</style> 