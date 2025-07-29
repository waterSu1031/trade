<script lang="ts">
  export let variant: 'primary' | 'secondary' | 'success' | 'danger' = 'primary';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let disabled: boolean = false;
  export let loading: boolean = false;
  export let className: string = '';
  
  $: sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  }[size];
</script>

<button
  class="ibkr-btn ibkr-btn-{variant} {sizeClasses} {className}"
  {disabled}
  class:opacity-50={disabled || loading}
  class:cursor-not-allowed={disabled || loading}
  on:click
>
  {#if loading}
    <span class="inline-block animate-spin rounded-full h-3 w-3 border-b-2 border-current mr-2"></span>
  {/if}
  <slot />
</button>