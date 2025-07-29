<script lang="ts">
  export let variant: 'success' | 'danger' | 'warning' | 'info' = 'info';
  export let size: 'sm' | 'md' = 'sm';
  export let className: string = '';
  
  $: sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1'
  }[size];
</script>

<span class="ibkr-badge ibkr-badge-{variant} {sizeClasses} {className}">
  <slot />
</span>