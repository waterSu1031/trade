<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';
</script>

<div class="min-h-screen bg-ibkr-background">
  <!-- Navigation -->
  <nav class="nav-container">
    <div class="container mx-auto flex items-center justify-between">
      <!-- Logo and Brand -->
      <div class="flex items-center">
        <a href="/" class="flex items-center px-4 py-3 text-ibkr-text hover:text-ibkr-primary transition-colors">
          <span class="text-lg font-semibold">Trading Dashboard</span>
        </a>
      </div>
      
      <!-- Navigation Links -->
      <div class="hidden md:flex items-center">
        <a 
          href="/trading" 
          class="nav-item {$page.url.pathname === '/trading' ? 'nav-item-active' : ''}"
        >
          Trading
        </a>
        <a 
          href="/strategy" 
          class="nav-item {$page.url.pathname === '/strategy' ? 'nav-item-active' : ''}"
        >
          Strategy
        </a>
        <a 
          href="/batch" 
          class="nav-item {$page.url.pathname === '/batch' ? 'nav-item-active' : ''}"
        >
          Batch Jobs
        </a>
        <a 
          href="/backtest" 
          class="nav-item {$page.url.pathname === '/backtest' ? 'nav-item-active' : ''}"
        >
          Backtest
        </a>
        <a 
          href="/statistics" 
          class="nav-item {$page.url.pathname === '/statistics' ? 'nav-item-active' : ''}"
        >
          Statistics
        </a>
      </div>
      
      <!-- Right Side Items -->
      <div class="flex items-center space-x-4 px-4">
        <!-- Connection Status -->
        <div class="flex items-center space-x-2">
          <div class="w-2 h-2 rounded-full bg-ibkr-success"></div>
          <span class="text-xs text-ibkr-text-secondary">Connected</span>
        </div>
        
        <!-- User Menu -->
        <div class="relative group">
          <button aria-label="User menu" class="flex items-center space-x-2 text-ibkr-text-secondary hover:text-ibkr-text">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
            </svg>
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </button>
          <div class="absolute right-0 mt-2 w-48 bg-ibkr-surface border border-ibkr-border rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
            <a href="/settings" class="block px-4 py-2 text-sm text-ibkr-text-secondary hover:bg-ibkr-background hover:text-ibkr-text">Settings</a>
            <a href="/account" class="block px-4 py-2 text-sm text-ibkr-text-secondary hover:bg-ibkr-background hover:text-ibkr-text">Account</a>
            <hr class="border-ibkr-border my-1" />
            <a href="/logout" class="block px-4 py-2 text-sm text-ibkr-text-secondary hover:bg-ibkr-background hover:text-ibkr-text">Logout</a>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Mobile Menu Toggle -->
    <div class="md:hidden px-4 pb-3">
      <button aria-label="Mobile menu" class="text-ibkr-text-secondary hover:text-ibkr-text">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
        </svg>
      </button>
    </div>
  </nav>

  <!-- Main Content -->
  <main class="container mx-auto px-4 py-6">
    <slot />
  </main>
</div>