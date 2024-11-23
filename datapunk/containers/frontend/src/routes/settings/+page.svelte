<script lang="ts">
    import { onMount } from 'svelte';
    import PageLayout from '$lib/components/layout/PageLayout.svelte';
    import { settings, type AppSettings } from '$lib/stores/settings';
    import type { ServiceSettings } from '$lib/types/services';
    import ErrorBoundary from '$lib/components/ErrorBoundary.svelte';
    
    let loading = true;
    let saving = false;
    let error: Error | null = null;
    
    onMount(async () => {
        try {
            await settings.load();
        } catch (err) {
            error = err instanceof Error ? err : new Error('Failed to load settings');
        } finally {
            loading = false;
        }
    });
    
    async function handleSave() {
        saving = true;
        try {
            await settings.save();
        } catch (err) {
            error = err instanceof Error ? err : new Error('Failed to save settings');
        } finally {
            saving = false;
        }
    }
</script>

<PageLayout
    title="Settings"
    description="Configure application settings and preferences"
    {loading}
>
    <ErrorBoundary>
        <div class="settings-container">
            <!-- Theme Settings -->
            <section class="settings-section">
                <h2>Theme</h2>
                <div class="setting-group">
                    <label>
                        Mode
                        <select
                            bind:value={$settings.theme.mode}
                            disabled={saving}
                        >
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                        </select>
                    </label>
                    
                    <label>
                        Accent Color
                        <input
                            type="color"
                            bind:value={$settings.theme.accentColor}
                            disabled={saving}
                        />
                    </label>
                </div>
            </section>
            
            <!-- Monitoring Settings -->
            <section class="settings-section">
                <h2>Monitoring</h2>
                <div class="setting-group">
                    <label>
                        Refresh Interval (seconds)
                        <input
                            type="number"
                            min="5"
                            max="300"
                            bind:value={$settings.monitoring.refreshInterval}
                            disabled={saving}
                        />
                    </label>
                    
                    <label>
                        Data Retention (days)
                        <input
                            type="number"
                            min="1"
                            max="90"
                            bind:value={$settings.monitoring.retentionPeriod}
                            disabled={saving}
                        />
                    </label>
                </div>
                
                <h3>Alert Thresholds</h3>
                <div class="setting-group">
                    <label>
                        CPU Usage (%)
                        <input
                            type="number"
                            min="0"
                            max="100"
                            bind:value={$settings.monitoring.alertThresholds.cpu}
                            disabled={saving}
                        />
                    </label>
                    
                    <label>
                        Memory Usage (%)
                        <input
                            type="number"
                            min="0"
                            max="100"
                            bind:value={$settings.monitoring.alertThresholds.memory}
                            disabled={saving}
                        />
                    </label>
                    
                    <label>
                        Error Rate (%)
                        <input
                            type="number"
                            min="0"
                            max="100"
                            bind:value={$settings.monitoring.alertThresholds.errorRate}
                            disabled={saving}
                        />
                    </label>
                    
                    <label>
                        Response Time (ms)
                        <input
                            type="number"
                            min="0"
                            bind:value={$settings.monitoring.alertThresholds.responseTime}
                            disabled={saving}
                        />
                    </label>
                </div>
            </section>
            
            <!-- Service Settings -->
            <section class="settings-section">
                <h2>Services</h2>
                {#each Object.entries($settings.services) as [serviceName, serviceSettings]}
                    <div class="service-settings">
                        <h3>{serviceName}</h3>
                        <div class="setting-group">
                            {#if serviceSettings}
                                {@const settings = serviceSettings as ServiceSettings}
                                <label>
                                    Max Retries
                                    <input
                                        type="number"
                                        min="0"
                                        max="10"
                                        bind:value={settings.maxRetries}
                                        disabled={saving}
                                    />
                                </label>
                                
                                <label>
                                    Timeout (seconds)
                                    <input
                                        type="number"
                                        min="1"
                                        max="300"
                                        bind:value={settings.timeout}
                                        disabled={saving}
                                    />
                                </label>
                                
                                <label class="checkbox-label">
                                    <input
                                        type="checkbox"
                                        bind:checked={settings.cacheEnabled}
                                        disabled={saving}
                                    />
                                    Enable Caching
                                </label>
                                
                                {#if settings.cacheEnabled}
                                    <label>
                                        Cache Duration (minutes)
                                        <input
                                            type="number"
                                            min="1"
                                            max="1440"
                                            bind:value={settings.cacheDuration}
                                            disabled={saving}
                                        />
                                    </label>
                                {/if}
                            {/if}
                        </div>
                    </div>
                {/each}
            </section>
            
            <div class="actions">
                <button
                    class="secondary"
                    on:click={() => settings.reset()}
                    disabled={saving}
                >
                    Reset to Defaults
                </button>
                <button
                    class="primary"
                    on:click={handleSave}
                    disabled={saving}
                >
                    {saving ? 'Saving...' : 'Save Changes'}
                </button>
            </div>
            
            {#if error}
                <div class="error-message">
                    {error.message}
                </div>
            {/if}
        </div>
    </ErrorBoundary>
</PageLayout>

<style>
    .settings-container {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .settings-section {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    
    .setting-group {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    label {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .checkbox-label {
        flex-direction: row;
        align-items: center;
    }
    
    input[type="number"],
    input[type="text"],
    select {
        padding: 0.5rem;
        border: 1px solid #e5e7eb;
        border-radius: 4px;
    }
    
    .actions {
        display: flex;
        justify-content: flex-end;
        gap: 1rem;
        margin-top: 2rem;
    }
    
    button {
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    
    button:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    
    .primary {
        background: #3b82f6;
        color: white;
    }
    
    .secondary {
        background: #e5e7eb;
        color: #374151;
    }
    
    .error-message {
        color: #ef4444;
        margin-top: 1rem;
        text-align: center;
    }
</style>
