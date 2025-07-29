<script lang="ts">
  // Test comment for monorepo structure verification - frontend project
  import { onMount } from 'svelte';
  import { dashboardApi, type DashboardSummary } from '$lib/api/dashboard';
  import Chart from 'chart.js/auto';
  import PriceTicker from '$lib/components/PriceTicker.svelte';
  import PositionMonitor from '$lib/components/PositionMonitor.svelte';
  import AlertNotifications from '$lib/components/AlertNotifications.svelte';
  import { initializeRealtime, cleanupRealtime, wsConnected } from '$lib/stores/realtime';
  
  let summary: DashboardSummary | null = null;
  let loading = true;
  let error: string | null = null;
  let chartCanvas: HTMLCanvasElement;
  let chart: Chart | null = null;
  
  async function loadDashboardData() {
    try {
      loading = true;
      error = null;
      summary = await dashboardApi.getSummary();
      
      // 차트 데이터 로드 및 업데이트
      if (chartCanvas && !chart) {
        const performanceData = await dashboardApi.getPerformance('1m', 'daily');
        
        chart = new Chart(chartCanvas, {
          type: 'line',
          data: {
            labels: performanceData.map(p => new Date(p.date).toLocaleDateString()),
            datasets: [{
              label: 'Portfolio Value',
              data: performanceData.map(p => p.equity),
              borderColor: '#0088cc',
              backgroundColor: 'rgba(0, 136, 204, 0.1)',
              tension: 0.1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              }
            },
            scales: {
              y: {
                beginAtZero: false,
                ticks: {
                  callback: function(value) {
                    return '$' + value.toLocaleString();
                  }
                }
              }
            }
          }
        });
      }
    } catch (err) {
      error = err instanceof Error ? err.message : '대시보드 데이터를 불러오는데 실패했습니다.';
      console.error('Dashboard error:', err);
    } finally {
      loading = false;
    }
  }
  
  function formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  }
  
  function formatPercent(value: number): string {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  }
  
  onMount(async () => {
    loadDashboardData();
    
    // Initialize real-time WebSocket connection
    await initializeRealtime();
    
    // 30초마다 데이터 새로고침
    const interval = setInterval(loadDashboardData, 30000);
    
    return () => {
      clearInterval(interval);
      cleanupRealtime();
      if (chart) {
        chart.destroy();
      }
    };
  });
</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex justify-between items-start">
    <div>
      <h1 class="text-3xl font-bold text-ibkr-text">트레이딩 대시보드</h1>
      <p class="text-ibkr-text-secondary mt-1">실시간 트레이딩 현황 및 성과 모니터링</p>
    </div>
    <div class="flex items-center gap-2">
      <div class="w-2 h-2 rounded-full {$wsConnected ? 'bg-profit' : 'bg-loss'}"></div>
      <span class="text-sm text-ibkr-text-secondary">
        {$wsConnected ? '실시간 연결됨' : '연결 끊김'}
      </span>
    </div>
  </div>

  {#if loading}
    <div class="flex justify-center items-center h-64">
      <div class="text-ibkr-text-secondary">Loading...</div>
    </div>
  {:else if error}
    <div class="custom-card border-ibkr-danger bg-ibkr-danger/10">
      <p class="text-ibkr-danger">{error}</p>
    </div>
  {:else if summary}
    <!-- 주요 지표 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="custom-card">
        <p class="text-sm text-ibkr-text-secondary">총 자산</p>
        <p class="text-2xl font-bold mt-1">{formatCurrency(summary.total_equity)}</p>
        <p class="text-xs text-ibkr-text-secondary mt-1">Net Liquidation Value</p>
      </div>
      
      <div class="custom-card">
        <p class="text-sm text-ibkr-text-secondary">일일 손익</p>
        <p class="text-2xl font-bold mt-1 {summary.daily_pnl >= 0 ? 'text-profit' : 'text-loss'}">
          {formatCurrency(summary.daily_pnl)}
        </p>
        <p class="text-xs {summary.daily_pnl >= 0 ? 'text-profit' : 'text-loss'} mt-1">
          {formatPercent(summary.daily_pnl_percent)}
        </p>
      </div>
      
      <div class="custom-card">
        <p class="text-sm text-ibkr-text-secondary">월간 손익</p>
        <p class="text-2xl font-bold mt-1 {summary.monthly_pnl >= 0 ? 'text-profit' : 'text-loss'}">
          {formatCurrency(summary.monthly_pnl)}
        </p>
        <p class="text-xs {summary.monthly_pnl >= 0 ? 'text-profit' : 'text-loss'} mt-1">
          {formatPercent(summary.monthly_pnl_percent)}
        </p>
      </div>
      
      <div class="custom-card">
        <p class="text-sm text-ibkr-text-secondary">승률</p>
        <p class="text-2xl font-bold mt-1">{summary.win_rate.toFixed(1)}%</p>
        <p class="text-xs text-ibkr-text-secondary mt-1">샤프비율: {summary.sharpe_ratio.toFixed(2)}</p>
      </div>
    </div>
    
    <!-- 차트 영역 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="custom-card">
        <h2 class="text-lg font-semibold mb-4">포트폴리오 가치 추이</h2>
        <div class="h-64">
          <canvas bind:this={chartCanvas}></canvas>
        </div>
      </div>
      
      <div class="custom-card">
        <h2 class="text-lg font-semibold mb-4">포지션 분포</h2>
        <div class="space-y-3">
          <div class="flex justify-between items-center">
            <span class="text-sm">Stocks</span>
            <div class="flex items-center gap-2">
              <div class="w-32 bg-ibkr-border rounded-full h-2">
                <div class="bg-ibkr-primary h-2 rounded-full" style="width: 60%"></div>
              </div>
              <span class="text-sm font-medium">60%</span>
            </div>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm">ETFs</span>
            <div class="flex items-center gap-2">
              <div class="w-32 bg-ibkr-border rounded-full h-2">
                <div class="bg-ibkr-info h-2 rounded-full" style="width: 25%"></div>
              </div>
              <span class="text-sm font-medium">25%</span>
            </div>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm">Options</span>
            <div class="flex items-center gap-2">
              <div class="w-32 bg-ibkr-border rounded-full h-2">
                <div class="bg-ibkr-secondary h-2 rounded-full" style="width: 10%"></div>
              </div>
              <span class="text-sm font-medium">10%</span>
            </div>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm">Cash</span>
            <div class="flex items-center gap-2">
              <div class="w-32 bg-ibkr-border rounded-full h-2">
                <div class="bg-gray-500 h-2 rounded-full" style="width: 5%"></div>
              </div>
              <span class="text-sm font-medium">5%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 추가 정보 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="custom-card">
        <div class="flex justify-between items-center">
          <span class="text-sm text-ibkr-text-secondary">활성 포지션</span>
          <span class="px-2 py-1 bg-ibkr-primary/20 text-ibkr-primary rounded text-xs font-medium">
            {summary.total_positions}
          </span>
        </div>
      </div>
      
      <div class="custom-card">
        <div class="flex justify-between items-center">
          <span class="text-sm text-ibkr-text-secondary">활성 전략</span>
          <span class="px-2 py-1 bg-ibkr-success/20 text-ibkr-success rounded text-xs font-medium">
            {summary.active_strategies}
          </span>
        </div>
      </div>
      
      <div class="custom-card">
        <div class="flex justify-between items-center">
          <span class="text-sm text-ibkr-text-secondary">최대 낙폭</span>
          <span class="px-2 py-1 bg-ibkr-danger/20 text-ibkr-danger rounded text-xs font-medium">
            {summary.max_drawdown.toFixed(1)}%
          </span>
        </div>
      </div>
      
      <div class="custom-card">
        <div class="flex justify-between items-center">
          <span class="text-sm text-ibkr-text-secondary">주간 손익</span>
          <span class="px-2 py-1 {summary.weekly_pnl >= 0 ? 'bg-ibkr-success/20 text-ibkr-success' : 'bg-ibkr-danger/20 text-ibkr-danger'} rounded text-xs font-medium">
            {formatPercent(summary.weekly_pnl_percent)}
          </span>
        </div>
      </div>
    </div>
    
    <!-- Real-time components section -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
      <!-- Price Ticker -->
      <div class="lg:col-span-1">
        <PriceTicker />
      </div>
      
      <!-- Position Monitor -->
      <div class="lg:col-span-2">
        <PositionMonitor />
      </div>
    </div>
  {/if}
</div>

<!-- Alert Notifications -->
<AlertNotifications position="top-right" />