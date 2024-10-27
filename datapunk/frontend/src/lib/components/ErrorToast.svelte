<script lang="ts">
    import { appStore } from '$lib/stores/appStore';
    import { fade } from 'svelte/transition';

    $: error = $appStore.error;
</script>

{#if error}
    <div class="toast" transition:fade>
        <p>{error}</p>
        <button on:click={() => appStore.setError(null)}>×</button>
    </div>
{/if}

<style>
    .toast {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        background: #ff5555;
        color: white;
        padding: 1rem;
        border-radius: 4px;
        display: flex;
        align-items: center;
        gap: 1rem;
        z-index: 1000;
    }

    button {
        background: none;
        border: none;
        color: white;
        font-size: 1.5rem;
        cursor: pointer;
    }
</style>