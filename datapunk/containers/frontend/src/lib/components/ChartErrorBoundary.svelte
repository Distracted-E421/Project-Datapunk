<script lang="ts">
    import type { D3Error } from '$lib/utils/d3-guards';
    import { onMount } from 'svelte';
    
    export let fallback: string = "Failed to render chart";
    export let onError: ((error: D3Error) => void) | null = null;
    
    let error: D3Error | null = null;
    
    function handleD3Error(event: ErrorEvent) {
        const err = event.error;
        if (err && 'type' in err) {
            error = err as D3Error;
            if (onError) {
                onError(error);
            }
        }
    }
    
    onMount(() => {
        window.addEventListener('error', handleD3Error);
        return () => {
            window.removeEventListener('error', handleD3Error);
        };
    });
</script>

{#if error}
    <div class="chart-error">
        <div class="error-content">
            <h3>{fallback}</h3>
            <p class="error-message">{error.message}</p>
            {#if error.context}
                <p class="error-context">Context: {error.context}</p>
            {/if}
            <button on:click={() => error = null}>
                Retry
            </button>
        </div>
    </div>
{:else}
    <slot />
{/if}

<style>
    .chart-error {
        padding: 1rem;
        background-color: #fee2e2;
        border: 1px solid #ef4444;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .error-content {
        text-align: center;
    }
    
    .error-message {
        color: #dc2626;
        margin: 0.5rem 0;
    }
    
    .error-context {
        color: #4b5563;
        font-size: 0.875rem;
    }
    
    button {
        background: #3b82f6;
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        margin-top: 0.5rem;
    }
    
    button:hover {
        background: #2563eb;
    }
</style> 