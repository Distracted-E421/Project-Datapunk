import { writable } from 'svelte/store';

interface AppState {
    theme: 'dark' | 'light';
    sidebarCollapsed: boolean;
    currentPage: string;
    isLoading: boolean;
    loadingMessage: string;
    error: string | null;
}

const initialState: AppState = {
    theme: 'dark',
    sidebarCollapsed: false,
    currentPage: 'home',
    isLoading: false,
    loadingMessage: '',
    error: null
};


// Create the store
const createAppStore = () => {
    const { subscribe, set, update } = writable<AppState>(initialState);

    return {
        subscribe,
        toggleTheme: () => update(state => ({
            ...state,
            theme: state.theme === 'dark' ? 'light' : 'dark'
        })),
        toggleSidebar: () => update(state => ({
            ...state,
            sidebarCollapsed: !state.sidebarCollapsed
        })),
        setCurrentPage: (page: string) => update(state => ({
            ...state,
            currentPage: page
        })),
        setLoading: (loading: boolean, message: string = '') => update(state => ({
            ...state,
            isLoading: loading,
            loadingMessage: message
        })),
        setError: (error: string | null) => update(state => ({
            ...state,
            error
        }))
    };
};

export const appStore = createAppStore();