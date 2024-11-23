/// <reference types="svelte" />
/// <reference types="vite/client" />

declare namespace svelteHTML {
    interface HTMLAttributes<T> {
        'on:click'?: (event: CustomEvent<any> & { target: EventTarget & T }) => void;
        'on:keypress'?: (event: CustomEvent<any> & { target: EventTarget & T }) => void;
        'on:mouseover'?: (event: CustomEvent<any> & { target: EventTarget & T }) => void;
        'on:mouseout'?: (event: CustomEvent<any> & { target: EventTarget & T }) => void;
        'bind:value'?: any;
        'bind:checked'?: boolean;
        'bind:this'?: any;
    }
} 