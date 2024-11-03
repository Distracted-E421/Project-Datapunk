<script lang="ts">
    import { appStore } from '../stores/appStore';
    import { fade } from 'svelte/transition';
    
    $: error = $appStore.error;
</script>

{#if error}
    <div class="toast-container" transition:fade>
        <div class="toast error">
            <span class="message">{error}</span>
            <button class="close" on:click={() => appStore.setError(null)}>×</button>
        </div>
    </div>
{/if}

<style>
    .toast-container {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        z-index: 1000;
    }

    .toast {
        background-color: #ff3e3e;
        color: white;
        padding: 1rem 2rem;
        border-radius: 4px;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    .close {
        background: none;
        border: none;
        color: white;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0;
    }

    .close:hover {
        opacity: 0.8;
    }
</style> 