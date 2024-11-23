<script lang="ts">
    import PageLayout from '$lib/components/layout/PageLayout.svelte';
    import { onMount } from 'svelte';
    import type { ServiceHealth } from '$lib/types/services';
    import ErrorBoundary from '$lib/components/ErrorBoundary.svelte';
    
    export let serviceName: string;
    export let serviceType: 'lake' | 'stream' | 'nexus';
    
    let health: ServiceHealth;
    let loading = true;
    let error: Error | null = null;
    
    onMount(async () => {
        try {
            const response = await fetch(`/api/services/${serviceType}/health`);
            health = await response.json();
        } catch (err) {
            error = err instanceof Error ? err : new Error('Failed to fetch service health');
        } finally {
            loading = false;
        }
    });
</script>

<PageLayout
    title="{serviceName}"
    description="Service health and configuration"
    {loading}
>
    <ErrorBoundary>
        {#if error}
            <div class="error-state">
                <h3>Error loading service data</h3>
                <p>{error.message}</p>
                <button on:click={() => window.location.reload()}>Retry</button>
            </div>
        {:else if health}
            <div class="service-details">
                <div class="status-card status-{health.status}">
                    <h3>Status: {health.status}</h3>
                    <p>Last checked: {new Date(health.lastCheck).toLocaleString()}</p>
                    {#if health.message}
                        <p class="message">{health.message}</p>
                    {/if}
                </div>
                
                {#if health.metrics}
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <span class="label">Response Time</span>
                            <span class="value">{health.metrics.responseTime}ms</span>
                        </div>
                        <div class="metric-card">
                            <span class="label">Uptime</span>
                            <span class="value">{health.metrics.uptime}%</span>
                        </div>
                        <div class="metric-card">
                            <span class="label">Error Rate</span>
                            <span class="value">{health.metrics.errorRate}%</span>
                        </div>
                    </div>
                {/if}
                
                <slot />
            </div>
        {/if}
    </ErrorBoundary>
</PageLayout>

<style>
    .service-details {
        display: flex;
        flex-direction: column;
        gap: 2rem;
    }
    
    .status-card {
        padding: 1.5rem;
        border-radius: 8px;
        background: white;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .status-healthy { border-left: 4px solid #10B981; }
    .status-degraded { border-left: 4px solid #F59E0B; }
    .status-unhealthy { border-left: 4px solid #EF4444; }
    
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    .label {
        font-size: 0.875rem;
        color: #6b7280;
    }
    
    .value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #111827;
        margin-top: 0.5rem;
    }
    
    .error-state {
        text-align: center;
        padding: 2rem;
    }
    
    button {
        margin-top: 1rem;
        padding: 0.5rem 1rem;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    
    button:hover {
        background: #2563eb;
    }
</style> 