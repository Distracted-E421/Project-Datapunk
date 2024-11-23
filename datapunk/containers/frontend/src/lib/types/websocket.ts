import type { WebSocketMessageEvent } from './d3';

export interface WebSocketMessage {
    type: string;
    data: any;
}

export interface WebSocketConfig {
    url: string;
    maxReconnectAttempts: number;
    baseDelay: number;
    maxDelay: number;
}

export interface WebSocketCallbacks {
    onMessage?: (event: MessageEvent) => void;
    onError?: (event: Event) => void;
    onClose?: () => void;
    onOpen?: () => void;
} 