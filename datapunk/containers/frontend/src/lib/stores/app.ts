import { writable } from 'svelte/store';

interface AppState {
    initialized: boolean;
    loading: boolean;
    error: Error | null;
    currentService: string | null;
    serviceStates: Record<string, 'healthy' | 'degraded' | 'unhealthy'>;
}

function createAppStore() {
    const { subscribe, set, update } = writable<AppState>({
        initialized: false,
        loading: false,
        error: null,
        currentService: null,
        serviceStates: {}
    });

    return {
        subscribe,
        initialize: () => update(state => ({ ...state, initialized: true })),
        setLoading: (loading: boolean) => update(state => ({ ...state, loading })),
        setError: (error: Error | null) => update(state => ({ ...state, error })),
        setCurrentService: (service: string | null) => 
            update(state => ({ ...state, currentService: service })),
        updateServiceState: (service: string, health: 'healthy' | 'degraded' | 'unhealthy') =>
            update(state => ({
                ...state,
                serviceStates: { ...state.serviceStates, [service]: health }
            })),
        reset: () => set({
            initialized: false,
            loading: false,
            error: null,
            currentService: null,
            serviceStates: {}
        })
    };
}

export const appStore = createAppStore(); 