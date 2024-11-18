const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            ...options.headers,
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
} 