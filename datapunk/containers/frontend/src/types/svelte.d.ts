declare module "*.svelte" {
    import type { ComponentType } from "svelte";
    const component: ComponentType;
    export default component;
}

declare module 'svelte' {
    export { SvelteComponent, onMount, onDestroy } from '@sveltejs/kit/types';
}

declare module 'svelte/store' {
    export { writable, readable, derived } from '@sveltejs/kit/types';
}

declare namespace svelteHTML {
    interface HTMLAttributes<T> {
        [key: string]: any;
    }
} 