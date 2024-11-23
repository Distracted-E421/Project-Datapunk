<script lang="ts">
    import ServicePage from '$lib/components/services/ServicePage.svelte';
    import TimeSeriesChart from '$lib/components/charts/TimeSeriesChart.svelte';
    import { onMount } from 'svelte';
    import { writable } from 'svelte/store';
    
    const storageMetrics = writable({
        diskUsage: [],
        queryPerformance: [],
        cacheHitRate: []
    });
    
    onMount(async () => {
        try {
            const response = await fetch('/api/services/lake/metrics');
            const data = await response.json();
            storageMetrics.set(data);
        } catch (error) {
            console.error('Failed to fetch lake metrics:', error);
        }
    });
</script>

<ServicePage 
    serviceName="Lake Service" 
    serviceType="lake"
>
    <div class="metrics-container">
        <div class="metric-card">
            <h3>Disk Usage Trend</h3>
            <TimeSeriesChart
                data={$storageMetrics.diskUsage}
                yLabel="Usage (%)"
                color="#3B82F6"
            />
        </div>
        
        <div class="metric-card">
            <h3>Query Performance</h3>
            <TimeSeriesChart
                data={$storageMetrics.queryPerformance}
                yLabel="Response Time (ms)"
                color="#10B981"
            />
        </div>
        
        <div class="metric-card">
            <h3>Cache Hit Rate</h3>
            <TimeSeriesChart
                data={$storageMetrics.cacheHitRate}
                yLabel="Hit Rate (%)"
                color="#8B5CF6"
            />
        </div>
    </div>
</ServicePage>

<style>
    .metrics-container {
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
    
    h3 {
        margin: 0 0 1rem 0;
        color: #111827;
    }
</style> 