<script lang="ts">
    import AppLayout from '$lib/components/layout/AppLayout.svelte';
    import { appStore } from '$lib/stores/app';
    import { onMount } from 'svelte';
    
    onMount(async () => {
        try {
            appStore.setLoading(true);
            // Initialize app state, fetch initial data, etc.
            await initializeApp();
            appStore.initialize();
        } catch (error) {
            if (error instanceof Error) {
                appStore.setError(error);
            }
        } finally {
            appStore.setLoading(false);
        }
    });
    
    async function initializeApp() {
        // Fetch initial app data, service states, etc.
    }
</script>

<AppLayout>
    <slot />
</AppLayout>