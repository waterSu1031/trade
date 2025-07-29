<script lang="ts">
  export let className: string = '';
  export let striped: boolean = false;
  export let hoverable: boolean = true;
</script>

<div class="overflow-x-auto">
  <table class="ibkr-table {className} {striped ? 'striped' : ''} {hoverable ? 'hoverable' : ''}">
    <slot />
  </table>
</div>

<style>
  :global(.ibkr-table.striped tbody tr:nth-child(even)) {
    background-color: rgba(42, 42, 42, 0.5);
  }
  
  :global(.ibkr-table.hoverable tbody tr:hover) {
    background-color: rgba(26, 26, 26, 0.5);
    cursor: pointer;
  }
</style>