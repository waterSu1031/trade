<script lang="ts">
  import { priceData, formatPrice } from '$lib/stores/realtime';
  import { fade } from 'svelte/transition';
  
  export let symbols: string[] = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY', 'QQQ'];
  
  // Track price changes
  let priceChanges: Record<string, 'up' | 'down' | 'neutral'> = {};
  let previousPrices: Record<string, number> = {};
  
  $: {
    // Update price change indicators
    Object.entries($priceData).forEach(([symbol, price]) => {
      if (previousPrices[symbol]) {
        if (price > previousPrices[symbol]) {
          priceChanges[symbol] = 'up';
        } else if (price < previousPrices[symbol]) {
          priceChanges[symbol] = 'down';
        } else {
          priceChanges[symbol] = 'neutral';
        }
        
        // Reset after animation
        setTimeout(() => {
          priceChanges[symbol] = 'neutral';
        }, 1000);
      }
      previousPrices[symbol] = price;
    });
  }
</script>

<div class="price-ticker">
  <div class="ticker-header">
    <h3 class="text-sm font-semibold text-ibkr-text-secondary">실시간 가격</h3>
  </div>
  
  <div class="ticker-content">
    {#each symbols as symbol}
      <div class="ticker-item" in:fade>
        <span class="symbol">{symbol}</span>
        {#if $priceData[symbol]}
          <span class="price {priceChanges[symbol] || 'neutral'}">
            {formatPrice($priceData[symbol])}
            {#if priceChanges[symbol] === 'up'}
              <svg class="price-arrow up" width="12" height="12" viewBox="0 0 12 12">
                <path d="M6 3L10 7H2L6 3Z" fill="currentColor"/>
              </svg>
            {:else if priceChanges[symbol] === 'down'}
              <svg class="price-arrow down" width="12" height="12" viewBox="0 0 12 12">
                <path d="M6 9L2 5H10L6 9Z" fill="currentColor"/>
              </svg>
            {/if}
          </span>
        {:else}
          <span class="price loading">--</span>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .price-ticker {
    @apply bg-ibkr-surface border border-ibkr-border rounded-md p-4;
  }
  
  .ticker-header {
    @apply mb-3 pb-2 border-b border-ibkr-border;
  }
  
  .ticker-content {
    @apply space-y-2;
  }
  
  .ticker-item {
    @apply flex justify-between items-center py-1;
  }
  
  .symbol {
    @apply text-sm font-medium text-ibkr-text;
  }
  
  .price {
    @apply text-sm font-mono transition-colors duration-300 flex items-center gap-1;
  }
  
  .price.neutral {
    @apply text-ibkr-text-secondary;
  }
  
  .price.up {
    @apply text-ibkr-success font-mono;
  }
  
  .price.down {
    @apply text-ibkr-danger font-mono;
  }
  
  .price.loading {
    @apply text-ibkr-text-secondary animate-pulse;
  }
  
  .price-arrow {
    @apply inline-block transition-transform duration-300;
  }
  
  .price-arrow.up {
    @apply text-ibkr-success animate-bounce;
  }
  
  .price-arrow.down {
    @apply text-ibkr-danger animate-bounce;
  }
</style>