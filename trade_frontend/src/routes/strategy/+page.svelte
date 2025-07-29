<script lang="ts">
  import { onMount } from 'svelte';
  import { strategyApi, type StrategyInfo, type StrategyPerformance } from '$lib/api/strategy';
  import IBKRCard from '$lib/components/IBKRCard.svelte';
  import IBKRButton from '$lib/components/IBKRButton.svelte';
  import IBKRStat from '$lib/components/IBKRStat.svelte';

  let strategies: StrategyInfo[] = [];
  let selectedStrategy: StrategyInfo | null = null;
  let performance: StrategyPerformance | null = null;
  let loading = false;
  let error = '';

  onMount(async () => {
    await loadStrategies();
  });

  async function loadStrategies() {
    loading = true;
    error = '';
    try {
      strategies = await strategyApi.getStrategies();
      if (strategies.length > 0 && !selectedStrategy) {
        await selectStrategy(strategies[0]);
      }
    } catch (e) {
      error = '전략 목록을 불러오는데 실패했습니다.';
      console.error(e);
    } finally {
      loading = false;
    }
  }

  async function selectStrategy(strategy: StrategyInfo) {
    selectedStrategy = strategy;
    try {
      performance = await strategyApi.getStrategyPerformance(strategy.name);
    } catch (e) {
      console.error('성과 데이터 로드 실패:', e);
      performance = null;
    }
  }

  async function toggleStrategy(strategy: StrategyInfo) {
    try {
      if (strategy.is_active) {
        await strategyApi.deactivateStrategy(strategy.name);
      } else {
        await strategyApi.activateStrategy(strategy.name);
      }
      await loadStrategies();
    } catch (e) {
      error = '전략 상태 변경에 실패했습니다.';
      console.error(e);
    }
  }

  function formatNumber(num: number | null | undefined): string {
    if (num === null || num === undefined) return 'N/A';
    return num.toFixed(2);
  }

  function formatPercent(num: number | null | undefined): string {
    if (num === null || num === undefined) return 'N/A';
    return `${num.toFixed(1)}%`;
  }
</script>

<div class="p-6">
  <h1 class="text-3xl font-bold mb-6">전략 관리</h1>

  {#if error}
    <div class="alert alert-error mb-4">
      <span>{error}</span>
    </div>
  {/if}

  <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- 전략 목록 -->
    <div class="lg:col-span-1">
      <IBKRCard>
        <h2 slot="title" class="text-xl font-semibold">전략 목록</h2>
        
        {#if loading}
          <div class="flex justify-center p-4">
            <span class="loading loading-spinner loading-lg"></span>
          </div>
        {:else}
          <div class="space-y-2">
            {#each strategies as strategy}
              <div 
                class="p-4 rounded-lg border cursor-pointer transition-colors"
                class:bg-base-200={selectedStrategy?.name === strategy.name}
                class:border-primary={selectedStrategy?.name === strategy.name}
                on:click={() => selectStrategy(strategy)}
                role="button"
                tabindex="0"
              >
                <div class="flex justify-between items-start">
                  <div>
                    <h3 class="font-semibold">{strategy.name}</h3>
                    <p class="text-sm text-base-content/70">{strategy.description}</p>
                    <p class="text-xs text-base-content/50 mt-1">v{strategy.version}</p>
                  </div>
                  <div class="badge" class:badge-success={strategy.is_active} class:badge-ghost={!strategy.is_active}>
                    {strategy.is_active ? '활성' : '비활성'}
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </IBKRCard>
    </div>

    <!-- 전략 상세 정보 -->
    <div class="lg:col-span-2">
      {#if selectedStrategy}
        <div class="space-y-6">
          <!-- 전략 컨트롤 -->
          <IBKRCard>
            <h2 slot="title" class="text-xl font-semibold">{selectedStrategy.name}</h2>
            
            <div class="space-y-4">
              <p class="text-base-content/70">{selectedStrategy.description}</p>
              
              <div class="flex gap-4">
                <IBKRButton
                  onClick={() => toggleStrategy(selectedStrategy)}
                  variant={selectedStrategy.is_active ? 'error' : 'success'}
                >
                  {selectedStrategy.is_active ? '비활성화' : '활성화'}
                </IBKRButton>
                
                <IBKRButton variant="secondary">
                  파라미터 수정
                </IBKRButton>
              </div>
            </div>
          </IBKRCard>

          <!-- 성과 지표 -->
          {#if performance}
            <IBKRCard>
              <h3 slot="title" class="text-lg font-semibold">성과 지표</h3>
              
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <IBKRStat
                  title="총 수익률"
                  value={formatPercent(performance.total_return)}
                  description="전체 기간"
                />
                <IBKRStat
                  title="샤프 비율"
                  value={formatNumber(performance.sharpe_ratio)}
                  description="위험 조정 수익률"
                />
                <IBKRStat
                  title="최대 낙폭"
                  value={formatPercent(performance.max_drawdown)}
                  description="최대 손실"
                />
                <IBKRStat
                  title="승률"
                  value={formatPercent(performance.win_rate)}
                  description="수익 거래 비율"
                />
              </div>

              <div class="divider"></div>

              <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                <IBKRStat
                  title="총 거래"
                  value={performance.total_trades.toString()}
                  description="전체 거래 수"
                />
                <IBKRStat
                  title="평균 수익"
                  value={`$${formatNumber(performance.avg_profit)}`}
                  description="거래당 평균"
                />
                <IBKRStat
                  title="수익 팩터"
                  value={formatNumber(performance.profit_factor)}
                  description="수익/손실 비율"
                />
              </div>
            </IBKRCard>
          {/if}

          <!-- 파라미터 -->
          <IBKRCard>
            <h3 slot="title" class="text-lg font-semibold">전략 파라미터</h3>
            
            <div class="space-y-2">
              {#each Object.entries(selectedStrategy.parameters) as [key, value]}
                <div class="flex justify-between items-center p-2 rounded bg-base-200">
                  <span class="font-medium">{key}:</span>
                  <span class="font-mono">{value}</span>
                </div>
              {/each}
            </div>
          </IBKRCard>
        </div>
      {:else}
        <div class="flex items-center justify-center h-64">
          <p class="text-base-content/50">전략을 선택해주세요</p>
        </div>
      {/if}
    </div>
  </div>
</div>