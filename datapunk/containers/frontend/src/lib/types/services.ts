export interface ServiceHealth {
    name: string;
    status: 'healthy' | 'degraded' | 'unhealthy';
    lastCheck: string;
    message?: string;
    metrics?: {
        responseTime: number;
        uptime: number;
        errorRate: number;
    };
}

export interface ServiceConfig {
    name: string;
    version: string;
    endpoint: string;
    healthCheck: string;
    dependencies: string[];
}

export interface ServiceError {
    code: string;
    message: string;
    timestamp: string;
    context?: Record<string, any>;
    retry?: boolean;
}

export interface ServiceResponse<T> {
    success: boolean;
    data?: T;
    error?: ServiceError;
    metadata?: {
        timestamp: string;
        version: string;
        processingTime: number;
    };
}

export interface ServiceSettings {
    maxRetries: number;
    timeout: number;  // in seconds
    cacheEnabled: boolean;
    cacheDuration: number;  // in minutes
} 