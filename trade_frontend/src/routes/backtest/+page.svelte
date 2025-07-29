<script lang="ts">
  import type { BacktestResult } from '$lib/types';
  import { onMount } from 'svelte';

  let results: BacktestResult[] = [];
  let selectedResult: BacktestResult | null = null;

  onMount(() => {
    results = [
      {
        id: '1',
        name: 'RSI 전략',
        startDate: new Date('2024-01-01'),
        endDate: new Date('2024-12-31'),
        totalReturn: 15.2,
        maxDrawdown: -8.5,
        sharpeRatio: 1.35,
        trades: []
      },
      {
        id: '2',
        name: 'MA 크로스 전략',
        startDate: new Date('2024-01-01'),
        endDate: new Date('2024-12-31'),
        totalReturn: 22.8,
        maxDrawdown: -12.3,
        sharpeRatio: 1.78,
        trades: []
      }
    ];
  });

  function selectResult(result: BacktestResult) {
    selectedResult = result;
  }

  function startNewBacktest() {
    // 새 백테스트 시작 로직
    console.log('새 백테스트 시작');
  }
</script>

<svelte:head>
  <title>백테스트 - 자동매매 시스템</title>
</svelte:head>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold">백테스트</h1>
    <button class="btn btn-primary" on:click={startNewBacktest}>
      새 백테스트 시작
    </button>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- 백테스트 목록 -->
    <div class="lg:col-span-1">
      <div class="card bg-base-100 shadow-lg">
        <div class="card-header p-4 border-b">
          <h2 class="card-title">백테스트 결과</h2>
        </div>
        <div class="card-body p-0">
          {#each results as result}
            <button 
              class="w-full p-4 text-left hover:bg-base-200 border-b last:border-b-0 {selectedResult?.id === result.id ? 'bg-primary/10' : ''}"
              on:click={() => selectResult(result)}
            >
              <div class="font-semibold">{result.name}</div>
              <div class="text-sm text-base-content/70">
                {result.startDate.toLocaleDateString()} - {result.endDate.toLocaleDateString()}
              </div>
              <div class="flex justify-between mt-2">
                <span class="text-sm">수익률:</span>
                <span class="text-sm font-mono {result.totalReturn >= 0 ? 'text-success' : 'text-error'}">
                  {result.totalReturn >= 0 ? '+' : ''}{result.totalReturn}%
                </span>
              </div>
            </button>
          {/each}
        </div>
      </div>
    </div>

    <!-- 백테스트 상세 정보 -->
    <div class="lg:col-span-2">
      {#if selectedResult}
        <div class="space-y-4">
          <!-- 성과 지표 -->
          <div class="card bg-base-100 shadow-lg">
            <div class="card-header p-4 border-b">
              <h2 class="card-title">{selectedResult.name} - 성과 지표</h2>
            </div>
            <div class="card-body">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="stat">
                  <div class="stat-title">총 수익률</div>
                  <div class="stat-value {selectedResult.totalReturn >= 0 ? 'text-success' : 'text-error'}">
                    {selectedResult.totalReturn >= 0 ? '+' : ''}{selectedResult.totalReturn}%
                  </div>
                </div>
                <div class="stat">
                  <div class="stat-title">최대 손실</div>
                  <div class="stat-value text-error">{selectedResult.maxDrawdown}%</div>
                </div>
                <div class="stat">
                  <div class="stat-title">샤프 비율</div>
                  <div class="stat-value text-info">{selectedResult.sharpeRatio}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 차트 영역 -->
          <div class="card bg-base-100 shadow-lg">
            <div class="card-header p-4 border-b">
              <h2 class="card-title">수익률 차트</h2>
            </div>
            <div class="card-body">
              <div class="h-64 flex items-center justify-center bg-base-200 rounded-lg">
                <p class="text-base-content/50">수익률 차트가 여기에 표시됩니다</p>
              </div>
            </div>
          </div>

          <!-- 거래 내역 -->
          <div class="card bg-base-100 shadow-lg">
            <div class="card-header p-4 border-b">
              <h2 class="card-title">거래 내역</h2>
            </div>
            <div class="card-body">
              <div class="h-32 flex items-center justify-center bg-base-200 rounded-lg">
                <p class="text-base-content/50">거래 내역이 여기에 표시됩니다</p>
              </div>
            </div>
          </div>
        </div>
      {:else}
        <div class="card bg-base-100 shadow-lg">
          <div class="card-body">
            <div class="h-64 flex items-center justify-center">
              <p class="text-base-content/50">백테스트 결과를 선택하세요</p>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>