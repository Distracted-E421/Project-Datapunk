<script lang="ts">
    import ChatInterface from '$lib/components/ChatInterface.svelte';
</script>

<div class="page">
    <h1>NeuroCortex Chat</h1>
    <div class="chat-container">
        <ChatInterface />
    </div>
</div>

<style>
    .page {
        padding: 2rem;
    }

    .chat-container {
        margin-top: 2rem;
        border: 1px solid var(--border);
        border-radius: 8px;
        height: 70vh;
    }
</style>