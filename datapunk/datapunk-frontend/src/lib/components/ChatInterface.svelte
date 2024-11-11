<script lang="ts">
    import { onMount } from 'svelte';
    import { appStore } from '../stores/appStore';

    let messages: Array<{text: string, sender: 'user' | 'ai', timestamp: Date}> = [];
    let inputMessage = '';
    let chatContainer: HTMLDivElement;

    // Websocket connection
    let ws: WebSocket;

    onMount(() => {
        connectWebSocket();
        return () => {
            if (ws) ws.close();
        };
    });

    function connectWebSocket() {
        ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/chat/${Date.now()}`);
        
        ws.onmessage = (event) => {
            const response = JSON.parse(event.data);
            messages = [...messages, {
                text: response.message,
                sender: 'ai',
                timestamp: new Date()
            }];
            scrollToBottom();
        };

        ws.onerror = (error) => {
            appStore.setError('Connection error. Please try again.');
        };
    }

    function sendMessage() {
        if (!inputMessage.trim()) return;
        
        messages = [...messages, {
            text: inputMessage,
            sender: 'user',
            timestamp: new Date()
        }];

        ws?.send(JSON.stringify({ message: inputMessage }));
        inputMessage = '';
        scrollToBottom();
    }

    function scrollToBottom() {
        setTimeout(() => {
            chatContainer?.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);
    }

    function handleKeyPress(event: KeyboardEvent) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    }
</script>

<div class="chat-interface">
    <div class="messages" bind:this={chatContainer}>
        {#each messages as message}
            <div class="message {message.sender}">
                <div class="bubble">
                    {message.text}
                </div>
                <div class="timestamp">
                    {message.timestamp.toLocaleTimeString()}
                </div>
            </div>
        {/each}
    </div>
    <div class="input-area">
        <textarea
            bind:value={inputMessage}
            on:keypress={handleKeyPress}
            placeholder="Type your message..."
            rows="3"
        />
        <button on:click={sendMessage} disabled={!inputMessage.trim()}>
            Send
        </button>
    </div>
</div>

<style>
    .chat-interface {
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    .messages {
        flex-grow: 1;
        overflow-y: auto;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .message {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        max-width: 70%;
    }

    .message.user {
        align-self: flex-end;
    }

    .message.ai {
        align-self: flex-start;
    }

    .bubble {
        padding: 0.75rem 1rem;
        border-radius: 1rem;
        background: var(--accent);
        color: white;
    }

    .message.ai .bubble {
        background: var(--bg-secondary);
        color: var(--text-primary);
    }

    .timestamp {
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-align: right;
    }

    .input-area {
        border-top: 1px solid var(--border);
        padding: 1rem;
        display: flex;
        gap: 1rem;
    }

    textarea {
        flex-grow: 1;
        padding: 0.75rem;
        border: 1px solid var(--border);
        border-radius: 4px;
        resize: none;
        background: var(--bg-secondary);
        color: var(--text-primary);
    }

    button {
        padding: 0.75rem 1.5rem;
        background: var(--accent);
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.2s;
    }

    button:hover:not(:disabled) {
        background: var(--accent-hover);
    }

    button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
</style>