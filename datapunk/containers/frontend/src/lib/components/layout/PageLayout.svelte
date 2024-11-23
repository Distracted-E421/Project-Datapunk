<script lang="ts">
    import ErrorBoundary from '$lib/components/ErrorBoundary.svelte';
    
    export let title: string;
    export let description: string = '';
    export let loading: boolean = false;
</script>

<div class="page-layout">
    <header class="page-header">
        <div class="header-content">
            <h1>{title}</h1>
            {#if description}
                <p class="description">{description}</p>
            {/if}
        </div>
        <div class="header-actions">
            <slot name="actions" />
        </div>
    </header>
    
    <main class="page-content">
        <ErrorBoundary>
            {#if loading}
                <div class="loading-state">
                    <span class="loader"></span>
                    <p>Loading...</p>
                </div>
            {:else}
                <slot />
            {/if}
        </ErrorBoundary>
    </main>
</div>

<style>
    .page-layout {
        padding: 2rem;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    
    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 2rem;
    }
    
    .header-content h1 {
        margin: 0;
        font-size: 1.875rem;
        font-weight: 600;
        color: #111827;
    }
    
    .description {
        margin-top: 0.5rem;
        color: #6b7280;
    }
    
    .page-content {
        flex: 1;
        min-height: 0;
    }
    
    .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: #6b7280;
    }
    
    .loader {
        border: 3px solid #f3f3f3;
        border-radius: 50%;
        border-top: 3px solid #3b82f6;
        width: 24px;
        height: 24px;
        animation: spin 1s linear infinite;
        margin-bottom: 1rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style> 