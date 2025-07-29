<script lang="ts">
  export let title: string;
  export let value: string | number;
  export let description: string = '';
  export let trend: 'up' | 'down' | 'neutral' = 'neutral';
  export let format: 'number' | 'currency' | 'percentage' = 'number';
  
  $: formattedValue = () => {
    if (typeof value === 'string') return value;
    
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 2
        }).format(value);
      case 'percentage':
        return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
      default:
        return value.toLocaleString();
    }
  };
  
  $: trendClass = {
    up: 'text-ibkr-success',
    down: 'text-ibkr-danger',
    neutral: 'text-ibkr-text'
  }[trend];
</script>

<div class="ibkr-stat">
  <div class="ibkr-stat-title">{title}</div>
  <div class="ibkr-stat-value {trendClass}">
    {formattedValue()}
  </div>
  {#if description}
    <div class="ibkr-stat-desc">{description}</div>
  {/if}
</div>