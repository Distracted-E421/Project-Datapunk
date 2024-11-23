<script lang="ts">
    import { onMount } from 'svelte';
    import PageLayout from '$lib/components/layout/PageLayout.svelte';
    import { appStore } from '$lib/stores/app';
    import type { ServiceHealth } from '$lib/types/services';
    
    let services: ServiceHealth[] = [];
    
    onMount(async () => {
        try {
            const response = await fetch('/api/services/health');
            services = await response.json();
        } catch (error) {
            if (error instanceof Error) {
                appStore.setError(error);
            }
        }
    });
</script>

<PageLayout 
    title="System Dashboard"
    description="Overview of all system components and their current status"
>
    <div class="dashboard-grid">
        {#each services as service}
            <div class="service-card status-{service.status}">
                <h2>{service.name}</h2>
                <div class="status-indicator">
                    <span class="status">{service.status}</span>
                    <span class="last-check">
                        Last checked: {new Date(service.lastCheck).toLocaleString()}
                    </span>
                </div>
                {#if service.message}
                    <p class="message">{service.message}</p>
                {/if}
                {#if service.metrics}
                    <div class="metrics">
                        <div class="metric">
                            <span class="label">Response Time</span>
                            <span class="value">{service.metrics.responseTime}ms</span>
                        </div>
                        <div class="metric">
                            <span class="label">Uptime</span>
                            <span class="value">{service.metrics.uptime}%</span>
                        </div>
                        <div class="metric">
                            <span class="label">Error Rate</span>
                            <span class="value">{service.metrics.errorRate}%</span>
                        </div>
                    </div>
                {/if}
            </div>
        {/each}
    </div>
</PageLayout>

<style>
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        padding: 1rem;
    }
    
    .service-card {
        background: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .status-healthy { border-left: 4px solid #10B981; }
    .status-degraded { border-left: 4px solid #F59E0B; }
    .status-unhealthy { border-left: 4px solid #EF4444; }
    
    .status-indicator {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 1rem 0;
    }
    
    .metrics {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #e5e7eb;
    }
    
    .metric {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    
    .label {
        font-size: 0.875rem;
        color: #6b7280;
    }
    
    .value {
        font-size: 1.25rem;
        font-weight: 600;
        color: #111827;
    }
</style>