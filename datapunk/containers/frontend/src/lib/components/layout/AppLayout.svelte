<script lang="ts">
    import { page } from '$app/stores';
    import { navigationConfig } from '$lib/types/navigation';
    import type { NavItem } from '$lib/types/navigation';
    import ErrorBoundary from '$lib/components/ErrorBoundary.svelte';
    
    let isNavOpen = false;
    
    function isActiveRoute(path: string): boolean {
        return $page.url.pathname.startsWith(path);
    }
    
    function toggleNav() {
        isNavOpen = !isNavOpen;
    }
    
    export let currentPath: string = '';
</script>

<div class="app-layout">
    <nav class:open={isNavOpen}>
        <div class="nav-header">
            <h1>DataPunk</h1>
            <button on:click={toggleNav}>
                <span class="sr-only">Toggle Navigation</span>
                <svg><!-- Menu icon --></svg>
            </button>
        </div>
        
        <ul class="nav-items">
            {#each navigationConfig as item}
                <li class="nav-item" class:active={isActiveRoute(item.path)}>
                    <a href={item.path}>
                        <span class="icon">{item.icon}</span>
                        <span class="label">{item.label}</span>
                    </a>
                    
                    {#if item.children}
                        <ul class="nav-children">
                            {#each item.children as child}
                                <li class:active={isActiveRoute(child.path)}>
                                    <a href={child.path}>
                                        <span class="icon">{child.icon}</span>
                                        <span class="label">{child.label}</span>
                                    </a>
                                </li>
                            {/each}
                        </ul>
                    {/if}
                </li>
            {/each}
        </ul>
    </nav>
    
    <main>
        <ErrorBoundary>
            <slot />
        </ErrorBoundary>
    </main>
</div>

<style>
    .app-layout {
        display: grid;
        grid-template-columns: auto 1fr;
        min-height: 100vh;
    }
    
    nav {
        background: #1a1a1a;
        color: white;
        width: 250px;
        padding: 1rem;
        transition: width 0.3s ease;
    }
    
    nav.open {
        width: 64px;
    }
    
    .nav-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }
    
    .nav-items {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .nav-item {
        margin-bottom: 0.5rem;
    }
    
    .nav-item a {
        display: flex;
        align-items: center;
        padding: 0.75rem;
        color: white;
        text-decoration: none;
        border-radius: 4px;
        transition: background-color 0.2s;
    }
    
    .nav-item a:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    
    .nav-item.active > a {
        background: rgba(255, 255, 255, 0.2);
    }
    
    main {
        padding: 2rem;
        background: #f8f9fa;
    }
</style> 