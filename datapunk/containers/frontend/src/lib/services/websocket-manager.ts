import { environment } from '$lib/config/environment';
import { errorTracking } from './error-tracking';

export class WebSocketManager {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private messageHandlers: Set<(data: any) => void> = new Set();

    constructor(private url: string) {}

    public connect() {
        try {
            this.ws = new WebSocket(this.url);
            this.setupEventHandlers();
        } catch (error) {
            if (error instanceof Error) {
                errorTracking.handleError(error, { context: 'WebSocket connection' });
            }
            this.scheduleReconnect();
        }
    }

    private setupEventHandlers() {
        if (!this.ws) return;

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };

        this.ws.onclose = () => {
            console.log('WebSocket closed');
            this.scheduleReconnect();
        };

        this.ws.onerror = (event) => {
            const error = new Error('WebSocket error occurred');
            errorTracking.handleError(error, { 
                context: 'WebSocket error',
                event 
            });
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.messageHandlers.forEach(handler => handler(data));
            } catch (error) {
                if (error instanceof Error) {
                    errorTracking.handleError(error, { context: 'WebSocket message parsing' });
                }
            }
        };
    }

    private scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            errorTracking.handleError(
                new Error('Max WebSocket reconnection attempts reached'),
                { context: 'WebSocket reconnection' }
            );
            return;
        }

        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        this.reconnectAttempts++;

        setTimeout(() => this.connect(), delay);
    }

    public addMessageHandler(handler: (data: any) => void) {
        this.messageHandlers.add(handler);
    }

    public removeMessageHandler(handler: (data: any) => void) {
        this.messageHandlers.delete(handler);
    }

    public close() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

export const wsManager = new WebSocketManager(environment.WS_URL); 