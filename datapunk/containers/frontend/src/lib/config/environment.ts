interface Environment {
    API_URL: string;
    WS_URL: string;
    NODE_ENV: 'development' | 'production' | 'test';
}

export const environment: Environment = {
    API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
    NODE_ENV: import.meta.env.MODE as 'development' | 'production' | 'test'
};

export const isDevelopment = environment.NODE_ENV === 'development';
export const isProduction = environment.NODE_ENV === 'production';
export const isTest = environment.NODE_ENV === 'test'; 