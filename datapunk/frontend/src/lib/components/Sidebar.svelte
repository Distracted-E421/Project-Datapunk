<script>
    let menuItems = [
        { label: 'Home', path: '/' },
        { label: 'Import', path: '/import' },
        { label: 'Analytics', path: '/analytics' },
        { label: 'Reports', path: '/reports' },
        { label: 'Settings', path: '/settings' }
    ];
</script>

<div class="sidebar">
    <div class="logo">
        DataPunk
    </div>
    <nav class="menu">
        {#each menuItems as item}
            <a href={item.path} class="menu-item">
                {item.label}
            </a>
        {/each}
    </nav>
</div>

<style>
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
    }

    .logo {
        font-size: 1.5rem;
        font-weight: bold;
        padding: 1rem;
        text-align: center;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1rem;
        color: var(--accent);
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
</style>