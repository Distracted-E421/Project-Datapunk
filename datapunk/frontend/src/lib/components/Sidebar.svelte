<script lang="ts">
    import { appStore } from '../stores/appStore';

    let menuItems = [
        { label: 'Home', path: '/' },
        { label: 'Import', path: '/import' },
        { label: 'Analytics', path: '/analytics' },
        { label: 'Reports', path: '/reports' },
        { label: 'Settings', path: '/settings' }
    ];

    // Subscribe to the store
    $: sidebarCollapsed = $appStore.sidebarCollapsed;

    function handleMenuClick(path: string) {
        appStore.setCurrentPage(path.replace('/', '') || 'home');
    }
    function toggleSidebar() {
        appStore.toggleSidebar();
    }
</script>

<div class="sidebar" class:collapsed={sidebarCollapsed}>
    <button class="toggle-btn" on:click={toggleSidebar}>
        {#if sidebarCollapsed}
            ▶
        {:else}
            ◀
        {/if}
    </button>
    <div class="logo">
        {#if !sidebarCollapsed}
            DataPunk
        {:else}
            DP
        {/if}
    </div>
    <nav class="menu">
        {#each menuItems as item}
            <a 
                href={item.path} 
                class="menu-item"
                on:click={() => handleMenuClick(item.path)}
            >
                {item.label}
            </a>
        {/each}
    </nav>
</div>

<style>
    .toggle-btn {
        position: absolute;
        right: -15px;
        top: 50%;
        transform: translateY(-50%);
        background: var(--accent);
        border: none;
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: background-color 0.2s;
    }

    .toggle-btn:hover {
        background: var(--accent-hover);
    }
    .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: 250px;
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        padding: 1rem;
        box-shadow: 2px 0 5px rgba(0, 0, 0, 0.2);
        transition: width 0.3s ease;
    }

    .sidebar.collapsed {
        width: 60px;
    }

    .logo {
        font-size: 2rem;
        font-weight: normal;
        padding: 1rem;
        text-align: center;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1rem;
        color: var(--accent);
        font-family: var(--font-title);
    }

    .menu {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .menu-item {
        padding: 0.75rem 1rem;
        color: var(--text-primary);
        text-decoration: none;
        border-radius: 4px;
        transition: background-color 0.2s;
    }

    .menu-item:hover {
        background-color: var(--accent);
        color: white;
    }

    .collapsed .menu-item {
        padding: 0.75rem;
        text-align: center;
    }
</style>