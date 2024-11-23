<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { browser } from '$app/environment';
    
    export let fallback = "Something went wrong";
    export let onError: ((error: Error) => void) | null = null;
    
    let error: Error | null = null;
    let errorInfo: string = '';
    
    function handleError(event: ErrorEvent) {
        error = event.error;
        errorInfo = event.error.stack || '';
        if (onError) {
            onError(event.error);
        }
    }
    
    onMount(() => {
        if (browser) {
            window.addEventListener('error', handleError);
        }
    });
    
    onDestroy(() => {
        if (browser) {
            window.removeEventListener('error', handleError);
        }
    });
</script>

{#if error}
    <div class="error-boundary">
        <div class="error-content">
            <h2>{fallback}</h2>
            <p class="error-message">{error.message}</p>
            {#if errorInfo}
                <details>
                    <summary>Error Details</summary>
                    <pre>{errorInfo}</pre>
                </details>
            {/if}
            <button on:click={() => window.location.reload()}>
                Reload Page
            </button>
        </div>
    </div>
{:else}
    <slot />
{/if}

<style>
    .error-boundary {
        padding: 2rem;
        margin: 1rem;
        background-color: #fee2e2;
        border: 1px solid #ef4444;
        border-radius: 8px;
    }
    
    .error-content {
        text-align: center;
    }
    
    .error-message {
        color: #dc2626;
        margin: 1rem 0;
    }
    
    details {
        margin: 1rem 0;
        text-align: left;
    }
    
    pre {
        background: #1f2937;
        color: #f3f4f6;
        padding: 1rem;
        border-radius: 4px;
        overflow-x: auto;
    }
    
    button {
        background: #3b82f6;
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    
    button:hover {
        background: #2563eb;
    }
</style> 