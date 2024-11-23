export class ReconnectingWebSocket {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private baseDelay = 1000;
    private maxDelay = 30000;
    private url: string;
    private onMessageCallback: ((event: MessageEvent) => void) | null = null;
    private onErrorCallback: ((error: Event) => void) | null = null;
    
    constructor(url: string) {
        this.url = url;
    }
    
    connect(): void {
        try {
            this.ws = new WebSocket(this.url);
            this.ws.onmessage = this.handleMessage.bind(this);
            this.ws.onerror = this.handleError.bind(this);
            this.ws.onclose = this.handleClose.bind(this);
            this.ws.onopen = () => {
                this.reconnectAttempts = 0;
                console.log('WebSocket connected');
            };
        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.scheduleReconnect();
        }
    }
    
    private handleMessage(event: MessageEvent): void {
        if (this.onMessageCallback) {
            this.onMessageCallback(event);
        }
    }
    
    private handleError(event: Event): void {
        if (this.onErrorCallback) {
            this.onErrorCallback(event);
        }
    }
    
    private handleClose(): void {
        console.log('WebSocket closed');
        this.scheduleReconnect();
    }
    
    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }
        
        const delay = Math.min(
            this.baseDelay * Math.pow(2, this.reconnectAttempts),
            this.maxDelay
        );
        
        this.reconnectAttempts++;
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
        setTimeout(() => this.connect(), delay);
    }
    
    onMessage(callback: (event: MessageEvent) => void): void {
        this.onMessageCallback = callback;
    }
    
    onError(callback: (error: Event) => void): void {
        this.onErrorCallback = callback;
    }
    
    send(data: string | ArrayBufferLike | Blob | ArrayBufferView): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        } else {
            console.error('WebSocket is not connected');
        }
    }
    
    close(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
} 