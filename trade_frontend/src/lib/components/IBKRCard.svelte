<script lang="ts">
  export let title: string = '';
  export let className: string = '';
</script>

<div class="ibkr-card {className}">
  {#if title}
    <div class="ibkr-card-header">
      {title}
    </div>
  {/if}
  <div class="{title ? 'mt-4' : ''}">
    <slot />
  </div>
</div>