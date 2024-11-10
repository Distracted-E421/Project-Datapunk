<script lang="ts">
    export let title: string;
    export let minimizable = false;
    export let closable = false;

    let minimized = false;

    function toggleMinimize() {
        minimized = !minimized;
    }
</script>

<div class="widget">
    <div class="widget-header">
        <h3>{title}</h3>
        <div class="controls">
            {#if minimizable}
                <button on:click={toggleMinimize}>
                    {minimized ? '+' : '-'}
                </button>
            {/if}
            {#if closable}
                <button on:click={() => dispatch('close')}>×</button>
            {/if}
        </div>
    </div>
    
    {#if !minimized}
        <div class="widget-content">
            <slot />
        </div>
    {/if}
</div>

<style>
    .widget {
        background: var(--bg-secondary);
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }

    .widget-header {
        padding: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid var(--border);
    }

    .widget-header h3 {
        margin: 0;
        font-family: var(--font-title);
        color: var(--accent);
    }

    .controls {
        display: flex;
        gap: 0.5rem;
    }

    .controls button {
        background: none;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        padding: 0.25rem 0.5rem;
    }

    .controls button:hover {
        color: var(--text-primary);
    }

    .widget-content {
        padding: 1rem;
    }
</style>