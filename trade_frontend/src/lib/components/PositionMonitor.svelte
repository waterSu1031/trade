<script lang="ts">
  import { positionData, totalPortfolioValue, totalPnL, formatPrice, formatPercent } from '$lib/stores/realtime';
  import { fade, fly } from 'svelte/transition';
  
  // Calculate total P&L percentage
  $: totalPnLPercent = $totalPortfolioValue > 0 
    ? ($totalPnL / ($totalPortfolioValue - $totalPnL)) * 100 
    : 0;
</script>

<div class="position-monitor">
  <div class="monitor-header">
    <h3 class="text-lg font-semibold text-ibkr-text">실시간 포지션</h3>
    <div class="header-stats">
      <div class="stat">
        <span class="label">총 가치</span>
        <span class="value">{formatPrice($totalPortfolioValue)}</span>
      </div>
      <div class="stat">
        <span class="label">총 손익</span>
        <span class="value {$totalPnL >= 0 ? 'profit' : 'loss'}">
          {formatPrice($totalPnL)}
          <span class="percent">({formatPercent(totalPnLPercent)})</span>
        </span>
      </div>
    </div>
  </div>
  
  {#if $positionData.length > 0}
    <div class="position-table">
      <div class="table-header">
        <div class="col-symbol">심볼</div>
        <div class="col-qty">수량</div>
        <div class="col-price">평균가</div>
        <div class="col-price">현재가</div>
        <div class="col-pnl">손익</div>
        <div class="col-percent">수익률</div>
      </div>
      
      <div class="table-body">
        {#each $positionData as position (position.symbol)}
          <div class="table-row" in:fly={{ y: 20, duration: 300 }}>
            <div class="col-symbol font-medium">{position.symbol}</div>
            <div class="col-qty">{position.qty}</div>
            <div class="col-price">{formatPrice(position.avg_price)}</div>
            <div class="col-price">{formatPrice(position.current_price)}</div>
            <div class="col-pnl {position.unrealized_pnl >= 0 ? 'profit' : 'loss'}">
              {formatPrice(position.unrealized_pnl)}
            </div>
            <div class="col-percent {position.pnl_percent >= 0 ? 'profit' : 'loss'}">
              {formatPercent(position.pnl_percent)}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {:else}
    <div class="empty-state" in:fade>
      <p class="text-ibkr-text-secondary text-center py-8">
        포지션이 없습니다
      </p>
    </div>
  {/if}
</div>

<style>
  .position-monitor {
    @apply bg-ibkr-surface border border-ibkr-border rounded-md overflow-hidden;
  }
  
  .monitor-header {
    @apply p-4 border-b border-ibkr-border flex justify-between items-center;
  }
  
  .header-stats {
    @apply flex gap-6;
  }
  
  .stat {
    @apply flex flex-col items-end;
  }
  
  .stat .label {
    @apply text-xs text-ibkr-text-secondary;
  }
  
  .stat .value {
    @apply text-sm font-semibold;
  }
  
  .stat .percent {
    @apply text-xs ml-1;
  }
  
  .position-table {
    @apply overflow-x-auto;
  }
  
  .table-header {
    @apply flex bg-ibkr-background px-4 py-2 text-xs font-medium text-ibkr-text-secondary uppercase tracking-wider;
  }
  
  .table-body {
    @apply divide-y divide-ibkr-border;
  }
  
  .table-row {
    @apply flex px-4 py-3 hover:bg-ibkr-background/50 transition-colors;
  }
  
  .col-symbol {
    @apply flex-1 min-w-[80px];
  }
  
  .col-qty {
    @apply w-20 text-right;
  }
  
  .col-price {
    @apply w-24 text-right font-mono text-sm;
  }
  
  .col-pnl {
    @apply w-28 text-right font-mono text-sm font-medium;
  }
  
  .col-percent {
    @apply w-20 text-right text-sm font-medium;
  }
  
  .profit {
    @apply text-ibkr-success font-mono;
  }
  
  .loss {
    @apply text-ibkr-danger font-mono;
  }
  
  .empty-state {
    @apply py-8;
  }
</style>