<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { tradesApi, statisticsApi, positionsApi, wsManager } from '$lib/api';
  import { tradingApi, type TradingSystemStatus, type AccountInfo, type OrderRequest } from '$lib/api/trading';
  import type { Trade, OverallStats, Position } from '$lib/api';
  import IBKRCard from '$lib/components/IBKRCard.svelte';
  import IBKRTable from '$lib/components/IBKRTable.svelte';
  import IBKRButton from '$lib/components/IBKRButton.svelte';
  import IBKRBadge from '$lib/components/IBKRBadge.svelte';
  import IBKRStat from '$lib/components/IBKRStat.svelte';

  let systemStatus: TradingSystemStatus | null = null;
  let accountInfo: AccountInfo | null = null;
  let recentTrades: Trade[] = [];
  let currentPositions: Position[] = [];
  let loading = true;
  let error: string | null = null;
  let unsubscribers: (() => void)[] = [];

  // 수동 주문 폼
  let orderForm: OrderRequest = {
    symbol: '',
    side: 'BUY',
    quantity: 100,
    order_type: 'MKT'
  };

  async function loadData() {
    try {
      loading = true;
      error = null;

      // 시스템 상태 조회
      systemStatus = await tradingApi.getStatus();
      
      // 계좌 정보 조회
      accountInfo = await tradingApi.getAccountInfo();

      // Load recent trades
      const tradesResponse = await tradesApi.getTrades(0, 20);
      if (tradesResponse.error) {
        throw new Error(tradesResponse.error);
      }

      // Load current positions
      const positionsResponse = await positionsApi.getPositions(true);
      if (positionsResponse.error) {
        throw new Error(positionsResponse.error);
      }

      recentTrades = tradesResponse.data || [];
      currentPositions = positionsResponse.data || [];
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load data';
      console.error('Error loading data:', err);
    } finally {
      loading = false;
    }
  }

  async function toggleTrading() {
    try {
      if (systemStatus?.status === 'running') {
        await tradingApi.stopTrading();
      } else {
        await tradingApi.startTrading(systemStatus?.mode || 'paper');
      }
      await loadData();
    } catch (err) {
      console.error('Error toggling trading:', err);
      error = 'Failed to change trading status';
    }
  }

  async function pauseResumeTrading() {
    try {
      if (systemStatus?.status === 'paused') {
        await tradingApi.resumeTrading();
      } else {
        await tradingApi.pauseTrading();
      }
      await loadData();
    } catch (err) {
      console.error('Error pausing/resuming trading:', err);
      error = 'Failed to pause/resume trading';
    }
  }

  async function placeManualOrder() {
    try {
      await tradingApi.placeOrder(orderForm);
      // Reset form
      orderForm = {
        symbol: '',
        side: 'BUY',
        quantity: 100,
        order_type: 'MKT'
      };
      await loadData();
    } catch (err) {
      console.error('Error placing order:', err);
      error = 'Failed to place order';
    }
  }

  async function cancelAllOrders() {
    if (confirm('정말로 모든 미체결 주문을 취소하시겠습니까?')) {
      try {
        await tradingApi.cancelAllOrders();
        await loadData();
      } catch (err) {
        console.error('Error cancelling orders:', err);
        error = 'Failed to cancel orders';
      }
    }
  }

  async function closeAllPositions() {
    if (confirm('정말로 모든 포지션을 청산하시겠습니까?')) {
      try {
        await tradingApi.closeAllPositions();
        await loadData();
      } catch (err) {
        console.error('Error closing positions:', err);
        error = 'Failed to close positions';
      }
    }
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  }

  function formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  }

  onMount(() => {
    loadData();

    // Connect WebSocket
    wsManager.connect();

    // Subscribe to real-time updates
    unsubscribers.push(
      wsManager.subscribe('trade_updates', (data) => {
        console.log('New trade:', data);
        loadData();
      })
    );

    unsubscribers.push(
      wsManager.subscribe('position_updates', (data) => {
        console.log('Position update:', data);
        loadData();
      })
    );

    // Refresh data every 10 seconds
    const interval = setInterval(loadData, 10000);

    return () => {
      clearInterval(interval);
    };
  });

  onDestroy(() => {
    unsubscribers.forEach(unsub => unsub());
  });
</script>

<svelte:head>
  <title>Trading Control - Trading Dashboard</title>
</svelte:head>

<div class="space-y-6">
  <!-- Page Header -->
  <div class="flex justify-between items-center mb-6">
    <div>
      <h1 class="text-2xl font-semibold text-ibkr-text">Trading Control</h1>
      <p class="text-sm text-ibkr-text-secondary mt-1">시스템 상태 및 트레이딩 컨트롤</p>
    </div>
    <div class="flex gap-2">
      {#if systemStatus?.status === 'running' || systemStatus?.status === 'paused'}
        <IBKRButton 
          variant="warning"
          on:click={pauseResumeTrading}
          disabled={loading}
        >
          {systemStatus?.status === 'paused' ? '재개' : '일시정지'}
        </IBKRButton>
      {/if}
      <IBKRButton 
        variant={systemStatus?.status === 'running' ? 'danger' : 'success'}
        on:click={toggleTrading}
        disabled={loading}
      >
        {systemStatus?.status === 'running' ? '트레이딩 중지' : '트레이딩 시작'}
      </IBKRButton>
    </div>
  </div>

  {#if loading}
    <div class="flex justify-center items-center h-64">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-ibkr-primary"></div>
    </div>
  {:else if error}
    <div class="ibkr-card border-ibkr-danger bg-ibkr-danger/10">
      <div class="flex items-center space-x-3">
        <svg class="w-5 h-5 text-ibkr-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <span class="text-ibkr-danger">{error}</span>
      </div>
    </div>
  {/if}

  <!-- System Status -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <IBKRCard>
      <div class="flex items-center justify-between">
        <div>
          <p class="text-xs text-ibkr-text-secondary uppercase mb-1">시스템 상태</p>
          <IBKRBadge variant={systemStatus?.status === 'running' ? 'success' : systemStatus?.status === 'paused' ? 'warning' : 'danger'}>
            {systemStatus?.status?.toUpperCase() || 'UNKNOWN'}
          </IBKRBadge>
        </div>
        <div class="text-2xl {systemStatus?.status === 'running' ? 'text-ibkr-success' : 'text-ibkr-danger'}">
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            {#if systemStatus?.status === 'running'}
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
            {:else}
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
            {/if}
          </svg>
        </div>
      </div>
    </IBKRCard>

    <IBKRCard>
      <div>
        <p class="text-xs text-ibkr-text-secondary uppercase mb-1">트레이딩 모드</p>
        <p class="text-lg font-semibold">
          <IBKRBadge variant={systemStatus?.mode === 'live' ? 'danger' : 'info'}>
            {systemStatus?.mode?.toUpperCase() || 'N/A'}
          </IBKRBadge>
        </p>
      </div>
    </IBKRCard>

    <IBKRCard>
      <div>
        <p class="text-xs text-ibkr-text-secondary uppercase mb-1">IBKR 연결</p>
        <p class="text-lg font-semibold">
          <IBKRBadge variant={systemStatus?.ibkr_connected ? 'success' : 'danger'}>
            {systemStatus?.ibkr_connected ? '연결됨' : '연결 끊김'}
          </IBKRBadge>
        </p>
      </div>
    </IBKRCard>

    <IBKRCard>
      <div>
        <p class="text-xs text-ibkr-text-secondary uppercase mb-1">활성 전략</p>
        <p class="text-lg font-semibold">{systemStatus?.active_strategies?.length || 0}개</p>
      </div>
    </IBKRCard>
  </div>

  <!-- Account Info -->
  {#if accountInfo}
    <IBKRCard>
      <h2 slot="title" class="text-lg font-semibold">계좌 정보</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <IBKRStat
          title="순자산"
          value={formatCurrency(accountInfo.net_liquidation)}
          description="Net Liquidation"
        />
        <IBKRStat
          title="현금"
          value={formatCurrency(accountInfo.total_cash)}
          description="Total Cash"
        />
        <IBKRStat
          title="구매력"
          value={formatCurrency(accountInfo.buying_power)}
          description="Buying Power"
        />
        <IBKRStat
          title="일일 손익"
          value={formatCurrency(accountInfo.daily_pnl)}
          description="Daily P&L"
          trend={accountInfo.daily_pnl >= 0 ? 'up' : 'down'}
        />
      </div>
    </IBKRCard>
  {/if}

  <!-- Quick Actions -->
  <IBKRCard>
    <h2 slot="title" class="text-lg font-semibold">빠른 실행</h2>
    <div class="flex gap-4 flex-wrap">
      <IBKRButton variant="danger" on:click={cancelAllOrders}>
        모든 주문 취소
      </IBKRButton>
      <IBKRButton variant="danger" on:click={closeAllPositions}>
        모든 포지션 청산
      </IBKRButton>
    </div>
  </IBKRCard>

  <!-- Manual Order -->
  <IBKRCard>
    <h2 slot="title" class="text-lg font-semibold">수동 주문</h2>
    <form on:submit|preventDefault={placeManualOrder} class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div>
        <label class="block text-sm font-medium mb-1">종목</label>
        <input
          type="text"
          bind:value={orderForm.symbol}
          class="input input-bordered w-full"
          placeholder="AAPL"
          required
        />
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">방향</label>
        <select bind:value={orderForm.side} class="select select-bordered w-full">
          <option value="BUY">매수</option>
          <option value="SELL">매도</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">수량</label>
        <input
          type="number"
          bind:value={orderForm.quantity}
          class="input input-bordered w-full"
          min="1"
          required
        />
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">주문 유형</label>
        <select bind:value={orderForm.order_type} class="select select-bordered w-full">
          <option value="MKT">시장가</option>
          <option value="LMT">지정가</option>
          <option value="STP">손절가</option>
        </select>
      </div>
      <div class="flex items-end">
        <IBKRButton type="submit" variant="primary" class="w-full">
          주문 실행
        </IBKRButton>
      </div>
    </form>
  </IBKRCard>

  <!-- Current Positions -->
  <IBKRCard title="현재 포지션">
    <IBKRTable striped>
      <thead>
        <tr>
          <th>종목</th>
          <th class="text-right">수량</th>
          <th class="text-right">평균가</th>
          <th class="text-right">현재가</th>
          <th class="text-right">미실현 손익</th>
          <th class="text-right">변동률</th>
        </tr>
      </thead>
      <tbody>
        {#if currentPositions.length > 0}
          {#each currentPositions as position}
            <tr>
              <td class="font-medium text-ibkr-text">{position.symbol}</td>
              <td class="text-right font-mono">{position.quantity.toLocaleString()}</td>
              <td class="text-right font-mono">${position.average_cost.toFixed(2)}</td>
              <td class="text-right font-mono">${position.market_price.toFixed(2)}</td>
              <td class="text-right font-mono {position.unrealized_pnl >= 0 ? 'profit' : 'loss'}">
                {position.unrealized_pnl >= 0 ? '+' : ''}${position.unrealized_pnl.toFixed(2)}
              </td>
              <td class="text-right font-mono {position.unrealized_pnl >= 0 ? 'profit' : 'loss'}">
                {((position.unrealized_pnl / (position.average_cost * position.quantity)) * 100).toFixed(2)}%
              </td>
            </tr>
          {/each}
        {:else}
          <tr>
            <td colspan="6" class="text-center text-ibkr-text-secondary py-8">
              포지션 없음
            </td>
          </tr>
        {/if}
      </tbody>
    </IBKRTable>
  </IBKRCard>

  <!-- Recent Trades -->
  <IBKRCard title="최근 거래">
    <IBKRTable>
      <thead>
        <tr>
          <th>시간</th>
          <th>종목</th>
          <th>방향</th>
          <th class="text-right">수량</th>
          <th class="text-right">가격</th>
          <th>상태</th>
          <th class="text-right">실현 손익</th>
        </tr>
      </thead>
      <tbody>
        {#if recentTrades.length > 0}
          {#each recentTrades as trade}
            <tr>
              <td class="font-mono text-xs text-ibkr-text-secondary">
                {formatDate(trade.execution_time || trade.created_at)}
              </td>
              <td class="font-medium text-ibkr-text">{trade.symbol}</td>
              <td>
                <IBKRBadge variant={trade.action === 'BUY' ? 'success' : 'danger'} size="sm">
                  {trade.action === 'BUY' ? '매수' : '매도'}
                </IBKRBadge>
              </td>
              <td class="text-right font-mono">{trade.quantity.toLocaleString()}</td>
              <td class="text-right font-mono">${trade.price.toFixed(2)}</td>
              <td>
                <IBKRBadge variant="success" size="sm">
                  {trade.status}
                </IBKRBadge>
              </td>
              <td class="text-right font-mono {trade.realized_pnl >= 0 ? 'profit' : 'loss'}">
                {trade.realized_pnl ? (trade.realized_pnl >= 0 ? '+' : '') + '$' + trade.realized_pnl.toFixed(2) : '-'}
              </td>
            </tr>
          {/each}
        {:else}
          <tr>
            <td colspan="7" class="text-center text-ibkr-text-secondary py-8">
              최근 거래 없음
            </td>
          </tr>
        {/if}
      </tbody>
    </IBKRTable>
  </IBKRCard>
</div>