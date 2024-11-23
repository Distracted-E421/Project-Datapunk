<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { writable } from 'svelte/store';
    import TimeSeriesChart from '$lib/components/charts/TimeSeriesChart.svelte';
    import GaugeChart from '$lib/components/charts/GaugeChart.svelte';
    import { ReconnectingWebSocket } from '$lib/utils/websocket';
    import type { MetricsData, Alert, WebSocketUpdate } from '$lib/types/monitoring';
    import type { WebSocketMessageEvent } from '$lib/types/d3';
    import ErrorBoundary from '$lib/components/ErrorBoundary.svelte';
    
    const metricsData = writable<MetricsData>({
        performance: [],
        resources: [],
        errors: [],
        loadTests: []
    });
    
    const alerts = writable<Alert[]>([]);
    let ws: ReconnectingWebSocket;
    
    onMount(async () => {
        try {
            const response = await fetch('/api/monitoring/metrics');
            const data: MetricsData = await response.json();
            metricsData.set(data);
            
            ws = new ReconnectingWebSocket(`ws://${window.location.host}/ws/monitoring`);
            ws.onMessage((event: WebSocketMessageEvent) => {
                const update = JSON.parse(event.data) as WebSocketUpdate;
                metricsData.update(current => ({
                    ...current,
                    [update.type]: [...current[update.type], update.data]
                }));
                
                if (update.alerts) {
                    alerts.set(update.alerts);
                }
            });
            
            ws.onError((error: Event) => {
                console.error('WebSocket error:', error);
                alerts.update(current => [
                    ...current,
                    {
                        id: crypto.randomUUID(),
                        severity: 'warning',
                        title: 'Connection Warning',
                        message: 'WebSocket connection error, attempting to reconnect...',
                        timestamp: new Date().toISOString()
                    }
                ]);
            });
            
            ws.connect();
            
        } catch (error) {
            console.error('Failed to initialize monitoring:', error);
            alerts.update(current => [
                ...current,
                {
                    id: crypto.randomUUID(),
                    severity: 'critical',
                    title: 'Connection Error',
                    message: 'Failed to connect to monitoring service',
                    timestamp: new Date().toISOString()
                }
            ]);
        }
    });
    
    onDestroy(() => {
        if (ws) {
            ws.close();
        }
    });
    
    $: currentCPU = $metricsData.resources[0]?.cpuUsage ?? 0;
    $: currentMemory = $metricsData.resources[0]?.memoryUsage ?? 0;
    
    function handleError(error: Error) {
        console.error('Monitoring error:', error);
        alerts.update(current => [
            ...current,
            {
                id: crypto.randomUUID(),
                severity: 'critical',
                title: 'Monitoring Error',
                message: error.message,
                timestamp: new Date().toISOString()
            }
        ]);
    }
</script>

<ErrorBoundary onError={handleError}>
    <div class="monitoring-dashboard">
        <header>
            <h1>System Monitoring</h1>
            
            <!-- Alerts Panel -->
            {#if $alerts.length > 0}
                <div class="alerts-panel">
                    {#each $alerts as alert}
                        <div class="alert alert-{alert.severity}">
                            <span class="alert-title">{alert.title}</span>
                            <span class="alert-message">{alert.message}</span>
                            <span class="alert-time">
                                {new Date(alert.timestamp).toLocaleString()}
                            </span>
                        </div>
                    {/each}
                </div>
            {/if}
        </header>
        
        <div class="metrics-grid">
            <ErrorBoundary fallback="Unable to load resource metrics">
                <div class="metric-card">
                    <h2>Resource Usage</h2>
                    <div class="gauge-grid">
                        <GaugeChart
                            value={currentCPU}
                            title="CPU Usage"
                            units="%"
                            thresholds={[
                                { value: 60, color: '#10B981' },
                                { value: 80, color: '#F59E0B' },
                                { value: 100, color: '#EF4444' }
                            ]}
                        />
                        <GaugeChart
                            value={currentMemory}
                            title="Memory Usage"
                            units="%"
                            thresholds={[
                                { value: 70, color: '#10B981' },
                                { value: 85, color: '#F59E0B' },
                                { value: 100, color: '#EF4444' }
                            ]}
                        />
                    </div>
                </div>
            </ErrorBoundary>
            
            <ErrorBoundary fallback="Unable to load performance metrics">
                <div class="metric-card">
                    <h2>Response Times</h2>
                    <TimeSeriesChart
                        data={$metricsData.performance}
                        xKey="timestamp"
                        yKey="responseTime"
                        title="Response Time Trend"
                        yLabel="Response Time (ms)"
                        color="#3B82F6"
                    />
                </div>
            </ErrorBoundary>
            
            <!-- Error Rates -->
            <ErrorBoundary fallback="Unable to load error metrics">
                <div class="metric-card">
                    <h2>Error Rates</h2>
                    <TimeSeriesChart
                        data={$metricsData.errors}
                        xKey="timestamp"
                        yKey="errorRate"
                        title="Error Rate Trend"
                        yLabel="Error Rate (%)"
                        color="#EF4444"
                    />
                </div>
            </ErrorBoundary>
            
            <!-- Load Test Results -->
            <ErrorBoundary fallback="Unable to load load test metrics">
                <div class="metric-card">
                    <h2>Load Test Results</h2>
                    <div class="load-test-grid">
                        {#each $metricsData.loadTests as test}
                            <div class="load-test-card">
                                <h3>{test.name}</h3>
                                <div class="test-metrics">
                                    <div class="metric">
                                        <span class="label">RPS:</span>
                                        <span class="value">{test.requestsPerSecond}</span>
                                    </div>
                                    <div class="metric">
                                        <span class="label">P95:</span>
                                        <span class="value">{test.p95ResponseTime}ms</span>
                                    </div>
                                    <div class="metric">
                                        <span class="label">Error Rate:</span>
                                        <span class="value">{test.errorRate}%</span>
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            </ErrorBoundary>
        </div>
    </div>
</ErrorBoundary>

<style>
    .monitoring-dashboard {
        padding: 2rem;
        max-width: 1600px;
        margin: 0 auto;
    }
    
    .alerts-panel {
        margin: 1rem 0;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .alert {
        padding: 0.75rem;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .alert-critical {
        background-color: #fee2e2;
        border: 1px solid #ef4444;
    }
    
    .alert-warning {
        background-color: #fef3c7;
        border: 1px solid #f59e0b;
    }
    
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
    
    .load-test-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }
    
    .load-test-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 4px;
    }
    
    .test-metrics {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    
    .metric {
        display: flex;
        justify-content: space-between;
    }
</style> 