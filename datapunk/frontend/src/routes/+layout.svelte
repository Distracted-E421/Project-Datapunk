<script>
    import Sidebar from '$lib/components/Sidebar.svelte';
    import '../app.css';
</script>

<div class="layout">
    <Sidebar />
    <main class="content">
        <slot />
    </main>
</div>

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
    }
</style>
