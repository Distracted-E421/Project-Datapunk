<script lang="ts">
    import Sidebar from '$lib/components/Sidebar.svelte';
    import { appStore } from '$lib/stores/appStore';
    import ErrorToast from '$lib/components/ErrorToast.svelte';
    import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
    import '../app.css';

    $: sidebarCollapsed = $appStore.sidebarCollapsed;
    $: error = $appStore.error;
    $: isLoading = $appStore.isLoading;
    $: loadingMessage = $appStore.loadingMessage;
</script>

<div class="layout">
    <Sidebar />
    <main class="content" class:sidebar-collapsed={sidebarCollapsed}>
        <slot />
    </main>
    {#if isLoading}
        <LoadingSpinner message={loadingMessage} />
    {/if}
    <ErrorToast />
    <style>
        .layout {
            display: flex;
            background-color: var(--bg-primary);
        }
    
        .content {
            margin-left: 250px;
            padding: 2rem;
            width: 100%;
            min-height: 100vh;
            transition: margin-left 0.3s ease;
        }
    
        .content.sidebar-collapsed {
            margin-left: 60px;
        }
    </style>
</div>