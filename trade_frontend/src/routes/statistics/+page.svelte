<script lang="ts">
  import type { Statistics } from '$lib/types';
  import { onMount } from 'svelte';

  let stats: Statistics = {
    dailyProfits: [],
    monthlyStats: [],
    symbolStats: []
  };

  onMount(() => {
    // 임시 데이터
    stats = {
      dailyProfits: [
        { date: '2024-01-01', profit: 1200 },
        { date: '2024-01-02', profit: -800 },
        { date: '2024-01-03', profit: 1500 },
        { date: '2024-01-04', profit: 2200 },
        { date: '2024-01-05', profit: -300 }
      ],
      monthlyStats: [
        { month: '2024-01', trades: 245, profit: 12500 },
        { month: '2024-02', trades: 198, profit: 8900 },
        { month: '2024-03', trades: 267, profit: 15600 }
      ],
      symbolStats: [
        { symbol: 'BTC/USDT', trades: 145, profit: 8500, winRate: 72.4 },
        { symbol: 'ETH/USDT', trades: 98, profit: 4200, winRate: 65.3 },
        { symbol: 'ADA/USDT', trades: 76, profit: -1200, winRate: 45.2 }
      ]
    };
  });
</script>

<svelte:head>
  <title>통계 - 자동매매 시스템</title>
</svelte:head>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold">통계</h1>
    <button class="btn btn-outline">
      리포트 내보내기
    </button>
  </div>

  <!-- 월별 통계 -->
  <div class="card bg-base-100 shadow-lg">
    <div class="card-header p-6 border-b">
      <h2 class="card-title">월별 통계</h2>
    </div>
    <div class="card-body p-0">
      <div class="overflow-x-auto">
        <table class="table table-zebra">
          <thead>
            <tr>
              <th>월</th>
              <th>거래 횟수</th>
              <th>총 수익</th>
              <th>평균 수익/거래</th>
            </tr>
          </thead>
          <tbody>
            {#each stats.monthlyStats as monthly}
              <tr>
                <td class="font-mono">{monthly.month}</td>
                <td class="font-mono">{monthly.trades}</td>
                <td class="font-mono {monthly.profit >= 0 ? 'text-success' : 'text-error'}">
                  ₩{monthly.profit.toLocaleString()}
                </td>
                <td class="font-mono">₩{Math.round(monthly.profit / monthly.trades).toLocaleString()}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- 심볼별 통계 -->
  <div class="card bg-base-100 shadow-lg">
    <div class="card-header p-6 border-b">
      <h2 class="card-title">심볼별 통계</h2>
    </div>
    <div class="card-body p-0">
      <div class="overflow-x-auto">
        <table class="table table-zebra">
          <thead>
            <tr>
              <th>심볼</th>
              <th>거래 횟수</th>
              <th>총 수익</th>
              <th>승률</th>
              <th>평균 수익/거래</th>
            </tr>
          </thead>
          <tbody>
            {#each stats.symbolStats as symbol}
              <tr>
                <td class="font-semibold">{symbol.symbol}</td>
                <td class="font-mono">{symbol.trades}</td>
                <td class="font-mono {symbol.profit >= 0 ? 'text-success' : 'text-error'}">
                  ₩{symbol.profit.toLocaleString()}
                </td>
                <td class="font-mono">{symbol.winRate}%</td>
                <td class="font-mono">₩{Math.round(symbol.profit / symbol.trades).toLocaleString()}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- 일별 수익률 차트 -->
  <div class="card bg-base-100 shadow-lg">
    <div class="card-header p-6 border-b">
      <h2 class="card-title">일별 수익률</h2>
    </div>
    <div class="card-body">
      <div class="h-64 flex items-center justify-center bg-base-200 rounded-lg">
        <p class="text-base-content/50">일별 수익률 차트가 여기에 표시됩니다</p>
      </div>
    </div>
  </div>

  <!-- 요약 통계 -->
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="stat bg-base-100 shadow-lg rounded-lg">
      <div class="stat-title">총 거래 횟수</div>
      <div class="stat-value text-primary">
        {stats.monthlyStats.reduce((sum, month) => sum + month.trades, 0)}
      </div>
    </div>

    <div class="stat bg-base-100 shadow-lg rounded-lg">
      <div class="stat-title">총 수익</div>
      <div class="stat-value text-success">
        ₩{stats.monthlyStats.reduce((sum, month) => sum + month.profit, 0).toLocaleString()}
      </div>
    </div>

    <div class="stat bg-base-100 shadow-lg rounded-lg">
      <div class="stat-title">평균 일별 수익</div>
      <div class="stat-value text-info">
        ₩{Math.round(stats.dailyProfits.reduce((sum, day) => sum + day.profit, 0) / stats.dailyProfits.length).toLocaleString()}
      </div>
    </div>

    <div class="stat bg-base-100 shadow-lg rounded-lg">
      <div class="stat-title">전체 승률</div>
      <div class="stat-value text-warning">
        {Math.round(stats.symbolStats.reduce((sum, symbol) => sum + (symbol.winRate * symbol.trades), 0) / stats.symbolStats.reduce((sum, symbol) => sum + symbol.trades, 0) * 100) / 100}%
      </div>
    </div>
  </div>
</div>