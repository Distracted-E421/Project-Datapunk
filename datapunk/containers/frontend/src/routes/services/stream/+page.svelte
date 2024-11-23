<script lang="ts">
    import ServicePage from '$lib/components/services/ServicePage.svelte';
    import TimeSeriesChart from '$lib/components/charts/TimeSeriesChart.svelte';
    import GaugeChart from '$lib/components/charts/GaugeChart.svelte';
    import { onMount, onDestroy } from 'svelte';
    import { writable, type Writable } from 'svelte/store';
    import type { ChartData } from '$lib/types/charts';
    import { wsManager } from '$lib/services/websocket-manager';
    
    interface StreamMetrics {
        throughput: ChartData[];
        latency: ChartData[];
        backpressure: ChartData[];
        processingTime: ChartData[];
        activeStreams: number;
        bufferUtilization: number;
        errorRate: number;
    }
    
    interface StreamUpdate {
        service: string;
        throughput?: ChartData;
        latency?: ChartData;
        backpressure?: ChartData;
        processingTime?: ChartData;
        activeStreams?: number;
        bufferUtilization?: number;
        errorRate?: number;
    }
    
    const metrics: Writable<StreamMetrics> = writable({
        throughput: [],
        latency: [],
        backpressure: [],
        processingTime: [],
        activeStreams: 0,
        bufferUtilization: 0,
        errorRate: 0
    });
    
    // Keep last 100 data points for real-time charts
    const MAX_DATA_POINTS = 100;
    
    onMount(async () => {
        try {
            // Load initial metrics
            const response = await fetch('/api/services/stream/metrics');
            const data = await response.json();
            metrics.set(data);
            
            // Subscribe to real-time updates
            wsManager.addMessageHandler(handleStreamUpdate);
            
        } catch (error) {
            console.error('Failed to load stream metrics:', error);
        }
    });
    
    onDestroy(() => {
        wsManager.removeMessageHandler(handleStreamUpdate);
    });
    
    function handleStreamUpdate(data: StreamUpdate) {
        if (data.service !== 'stream') return;
        
        metrics.update(current => {
            const updateTimeSeries = (key: keyof StreamMetrics) => {
                if (Array.isArray(current[key]) && data[key]) {
                    const newData = data[key] as unknown as ChartData;
                    return [...(current[key] as ChartData[]), newData];
                }
                return current[key];
            };
            
            return {
                throughput: updateTimeSeries('throughput') as ChartData[],
                latency: updateTimeSeries('latency') as ChartData[],
                backpressure: updateTimeSeries('backpressure') as ChartData[],
                processingTime: updateTimeSeries('processingTime') as ChartData[],
                activeStreams: data.activeStreams ?? current.activeStreams,
                bufferUtilization: data.bufferUtilization ?? current.bufferUtilization,
                errorRate: data.errorRate ?? current.errorRate
            };
        });
    }
</script>

<ServicePage 
    serviceName="Stream Service" 
    serviceType="stream"
>
    <div class="metrics-grid">
        <!-- Real-time Gauges -->
        <div class="metric-card">
            <h3>Current Status</h3>
            <div class="gauge-grid">
                <GaugeChart
                    value={$metrics.bufferUtilization}
                    title="Buffer Utilization"
                    units="%"
                    thresholds={[
                        { value: 60, color: '#10B981' },
                        { value: 80, color: '#F59E0B' },
                        { value: 100, color: '#EF4444' }
                    ]}
                />
                <GaugeChart
                    value={$metrics.errorRate}
                    title="Error Rate"
                    units="%"
                    max={10}
                    thresholds={[
                        { value: 2, color: '#10B981' },
                        { value: 5, color: '#F59E0B' },
                        { value: 10, color: '#EF4444' }
                    ]}
                />
            </div>
            <div class="active-streams">
                <span class="label">Active Streams:</span>
                <span class="value">{$metrics.activeStreams}</span>
            </div>
        </div>
        
        <!-- Throughput Chart -->
        <div class="metric-card">
            <h3>Stream Throughput</h3>
            <TimeSeriesChart
                data={$metrics.throughput}
                yLabel="Messages/sec"
                color="#3B82F6"
            />
        </div>
        
        <!-- Latency Chart -->
        <div class="metric-card">
            <h3>Stream Latency</h3>
            <TimeSeriesChart
                data={$metrics.latency}
                yLabel="Latency (ms)"
                color="#8B5CF6"
            />
        </div>
        
        <!-- Processing Time Chart -->
        <div class="metric-card">
            <h3>Processing Time</h3>
            <TimeSeriesChart
                data={$metrics.processingTime}
                yLabel="Processing Time (ms)"
                color="#10B981"
            />
        </div>
        
        <!-- Backpressure Chart -->
        <div class="metric-card">
            <h3>Backpressure</h3>
            <TimeSeriesChart
                data={$metrics.backpressure}
                yLabel="Queue Size"
                color="#F59E0B"
            />
        </div>
    </div>
</ServicePage>

<style>
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: 2rem;
        margin-top: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .gauge-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .active-streams {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
        margin-top: 1.5rem;
        padding: 1rem;
        background: #f8fafc;
        border-radius: 4px;
    }
    
    .label {
        font-size: 0.875rem;
        color: #6b7280;
    }
    
    .value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #111827;
    }
    
    h3 {
        margin: 0 0 1rem 0;
        color: #111827;
    }
</style> 