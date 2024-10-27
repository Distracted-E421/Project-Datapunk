<script lang="ts">
    export let message: string = '';
</script>

<div class="loading-overlay">
    <div class="spinner"></div>
    {#if message}
        <p class="message">{message}</p>
    {/if}
</div>

<style>
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.7);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .spinner {
        width: 50px;
        height: 50px;
        border: 3px solid var(--border);
        border-top-color: var(--accent);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    .message {
        margin-top: 1rem;
        color: var(--text-primary);
        font-family: var(--font-text);
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>