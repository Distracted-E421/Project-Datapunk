import { writable, get } from 'svelte/store';

interface ThemeSettings {
    mode: 'light' | 'dark';
    accentColor: string;
}

interface MonitoringSettings {
    refreshInterval: number;  // in seconds
    retentionPeriod: number; // in days
    alertThresholds: {
        cpu: number;
        memory: number;
        errorRate: number;
        responseTime: number;
    };
}

interface ServiceSettings {
    maxRetries: number;
    timeout: number;  // in seconds
    cacheEnabled: boolean;
    cacheDuration: number;  // in minutes
}

export interface AppSettings {
    theme: ThemeSettings;
    monitoring: MonitoringSettings;
    services: Record<string, ServiceSettings>;
}

const defaultSettings: AppSettings = {
    theme: {
        mode: 'light',
        accentColor: '#3B82F6'
    },
    monitoring: {
        refreshInterval: 30,
        retentionPeriod: 7,
        alertThresholds: {
            cpu: 80,
            memory: 85,
            errorRate: 5,
            responseTime: 1000
        }
    },
    services: {
        lake: {
            maxRetries: 3,
            timeout: 30,
            cacheEnabled: true,
            cacheDuration: 60
        },
        stream: {
            maxRetries: 3,
            timeout: 15,
            cacheEnabled: true,
            cacheDuration: 30
        },
        nexus: {
            maxRetries: 3,
            timeout: 20,
            cacheEnabled: true,
            cacheDuration: 45
        }
    }
};

function createSettingsStore() {
    const { subscribe, set, update } = writable<AppSettings>(defaultSettings);

    return {
        subscribe,
        updateTheme: (theme: Partial<ThemeSettings>) => 
            update(state => ({
                ...state,
                theme: { ...state.theme, ...theme }
            })),
        updateMonitoring: (monitoring: Partial<MonitoringSettings>) =>
            update(state => ({
                ...state,
                monitoring: { ...state.monitoring, ...monitoring }
            })),
        updateServiceSettings: (serviceName: string, settings: Partial<ServiceSettings>) =>
            update(state => ({
                ...state,
                services: {
                    ...state.services,
                    [serviceName]: { ...state.services[serviceName], ...settings }
                }
            })),
        reset: () => set(defaultSettings),
        async save() {
            try {
                const currentSettings = get(this);
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(currentSettings)
                });
            } catch (error) {
                console.error('Failed to save settings:', error);
                throw error;
            }
        },
        async load() {
            try {
                const response = await fetch('/api/settings');
                const settings = await response.json();
                set(settings);
            } catch (error) {
                console.error('Failed to load settings:', error);
                throw error;
            }
        }
    };
}

export const settings = createSettingsStore(); 