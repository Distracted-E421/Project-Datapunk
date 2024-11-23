<script lang="ts">
    import AppLayout from '$lib/components/layout/AppLayout.svelte';
    import { browser } from '$app/environment';
    import { page } from '$app/stores';
    
    // Only subscribe to page store on client side
    $: currentPath = browser ? $page.url.pathname : '';
</script>

<AppLayout {currentPath}>
    <slot />
</AppLayout>