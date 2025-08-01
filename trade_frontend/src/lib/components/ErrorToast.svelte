<script lang="ts">
  import { errorStore } from '$lib/stores/error';
  import { fade, fly } from 'svelte/transition';
</script>

<div class="toast toast-top toast-end z-50">
  {#each $errorStore as error (error.id)}
    <div 
      class="alert alert-{error.type === 'error' ? 'error' : error.type === 'warning' ? 'warning' : 'info'} shadow-lg"
      transition:fly={{ x: 100, duration: 300 }}
    >
      <div>
        <span>{error.message}</span>
      </div>
      <button 
        class="btn btn-ghost btn-xs"
        on:click={() => errorStore.removeError(error.id)}
      >
        ✕
      </button>
    </div>
  {/each}
</div>