import { writable } from 'svelte/store';

export interface AppSettings {
    theme: {
        mode: 'light' | 'dark';
        accentColor: string;
    };
    monitoring: {
        refreshInterval: number;
        retentionPeriod: number;
        alertThresholds: {
            cpu: number;
            memory: number;
            errorRate: number;
            responseTime: number;
        };
    };
    services: Record<string, ServiceSettings>;
}

const defaultSettings: AppSettings = {
    theme: {
        mode: 'light',
        accentColor: '#3B82F6'
    },
    monitoring: {
        refreshInterval: 5,
        retentionPeriod: 30,
        alertThresholds: {
            cpu: 80,
            memory: 80,
            errorRate: 5,
            responseTime: 1000
        }
    },
    services: {}
};

function createSettingsStore() {
    const { subscribe, set, update } = writable<AppSettings>(defaultSettings);

    return {
        subscribe,
        set,
        update,
        async load() {
            try {
                const response = await fetch('/api/settings');
                const data = await response.json();
                set(data);
            } catch (error) {
                console.error('Failed to load settings:', error);
                throw error;
            }
        },
        async save() {
            try {
                const currentSettings = get(this);
                await fetch('/api/settings', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(currentSettings)
                });
            } catch (error) {
                console.error('Failed to save settings:', error);
                throw error;
            }
        },
        reset() {
            set(defaultSettings);
        }
    };
}

export const settings = createSettingsStore(); 