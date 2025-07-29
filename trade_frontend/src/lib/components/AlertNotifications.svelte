<script lang="ts">
  import { alerts, alertColors } from '$lib/stores/realtime';
  import { fly, fade } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  
  export let maxAlerts = 5;
  export let position: 'top-right' | 'bottom-right' = 'top-right';
  
  // Get recent alerts
  $: recentAlerts = $alerts.slice(0, maxAlerts);
  
  // Dismiss alert
  function dismissAlert(alertId: string) {
    alerts.update(currentAlerts => 
      currentAlerts.filter(alert => alert.id !== alertId)
    );
  }
  
  // Get icon for severity
  function getIcon(severity: string) {
    switch(severity) {
      case 'critical':
        return '⚠️';
      case 'warning':
        return '⚡';
      case 'info':
      default:
        return 'ℹ️';
    }
  }
</script>

<div class="alert-container {position}">
  {#each recentAlerts as alert (alert.id)}
    <div 
      class="alert-item severity-{alert.severity}"
      in:fly={{ x: 300, duration: 300 }}
      out:fade={{ duration: 200 }}
      animate:flip={{ duration: 200 }}
    >
      <div class="alert-icon">
        {getIcon(alert.severity)}
      </div>
      
      <div class="alert-content">
        <div class="alert-header">
          <span class="alert-type">{alert.type}</span>
          {#if alert.symbol}
            <span class="alert-symbol">{alert.symbol}</span>
          {/if}
        </div>
        <p class="alert-message">{alert.message}</p>
        <time class="alert-time">
          {new Date(alert.timestamp).toLocaleTimeString()}
        </time>
      </div>
      
      <button 
        class="alert-dismiss"
        on:click={() => dismissAlert(alert.id)}
        aria-label="Dismiss alert"
      >
        ×
      </button>
    </div>
  {/each}
</div>

<style>
  .alert-container {
    @apply fixed z-50 space-y-2 p-4;
    max-width: 400px;
  }
  
  .alert-container.top-right {
    @apply top-0 right-0;
  }
  
  .alert-container.bottom-right {
    @apply bottom-0 right-0;
  }
  
  .alert-item {
    @apply bg-ibkr-surface border border-ibkr-border rounded-md p-3 shadow-lg flex gap-3 relative;
  }
  
  .alert-item.severity-info {
    @apply border-l-4 border-l-ibkr-info;
  }
  
  .alert-item.severity-warning {
    @apply border-l-4 border-l-ibkr-warning;
  }
  
  .alert-item.severity-critical {
    @apply border-l-4 border-l-ibkr-danger;
  }
  
  .alert-icon {
    @apply text-xl flex-shrink-0;
  }
  
  .alert-content {
    @apply flex-1;
  }
  
  .alert-header {
    @apply flex items-center gap-2 mb-1;
  }
  
  .alert-type {
    @apply text-xs font-medium text-ibkr-text-secondary uppercase;
  }
  
  .alert-symbol {
    @apply text-xs font-bold text-ibkr-primary;
  }
  
  .alert-message {
    @apply text-sm text-ibkr-text mb-1;
  }
  
  .alert-time {
    @apply text-xs text-ibkr-text-secondary;
  }
  
  .alert-dismiss {
    @apply absolute top-1 right-1 w-6 h-6 flex items-center justify-center text-ibkr-text-secondary hover:text-ibkr-text rounded-md hover:bg-ibkr-background transition-colors;
    font-size: 20px;
    line-height: 1;
  }
</style>