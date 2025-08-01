<script lang="ts">
  import { onMount } from 'svelte';
  import { positionsApi } from '$lib/api/positions';
  import { tradingApi } from '$lib/api/trading';
  import type { Position } from '$lib/api/positions';
  import type { TradingSystemStatus } from '$lib/api/trading';

  let positions: Position[] = [];
  let tradingStatus: TradingSystemStatus | null = null;
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      // Position API 테스트
      console.log('Position API 호출 중...');
      const positionResponse = await positionsApi.getPositions();
      console.log('Position API 응답:', positionResponse);
      
      if (positionResponse.data) {
        positions = positionResponse.data;
        console.log('포지션 데이터:', positions);
        
        // avg_cost 필드 확인
        if (positions.length > 0) {
          console.log('첫 번째 포지션 avg_cost:', positions[0].avg_cost);
        }
      }

      // Trading Status API 테스트
      console.log('Trading Status API 호출 중...');
      tradingStatus = await tradingApi.getStatus();
      console.log('Trading Status:', tradingStatus);

    } catch (e) {
      console.error('API 오류:', e);
      error = e instanceof Error ? e.message : '알 수 없는 오류';
    } finally {
      loading = false;
    }
  });
</script>

<div class="container mx-auto p-4">
  <h1 class="text-2xl font-bold mb-4">API 연결 테스트 페이지</h1>
  
  {#if loading}
    <p class="text-blue-500">데이터 로딩 중...</p>
  {:else if error}
    <p class="text-red-500">오류: {error}</p>
  {:else}
    <div class="space-y-6">
      <!-- Trading Status -->
      <div class="bg-gray-800 p-4 rounded">
        <h2 class="text-xl font-semibold mb-2">Trading Status</h2>
        {#if tradingStatus}
          <pre class="text-sm">{JSON.stringify(tradingStatus, null, 2)}</pre>
        {:else}
          <p>상태 정보 없음</p>
        {/if}
      </div>

      <!-- Positions -->
      <div class="bg-gray-800 p-4 rounded">
        <h2 class="text-xl font-semibold mb-2">Positions ({positions.length}개)</h2>
        {#if positions.length > 0}
          <div class="overflow-x-auto">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Quantity</th>
                  <th>Avg Cost</th>
                  <th>Market Price</th>
                  <th>Unrealized PnL</th>
                </tr>
              </thead>
              <tbody>
                {#each positions as position}
                  <tr>
                    <td>{position.symbol}</td>
                    <td>{position.quantity}</td>
                    <td>${position.avg_cost.toFixed(2)}</td>
                    <td>${position.market_price.toFixed(2)}</td>
                    <td class="{position.unrealized_pnl >= 0 ? 'text-green-500' : 'text-red-500'}">
                      ${position.unrealized_pnl.toFixed(2)}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
          
          <div class="mt-4">
            <h3 class="font-semibold">첫 번째 포지션 전체 데이터:</h3>
            <pre class="text-xs mt-2">{JSON.stringify(positions[0], null, 2)}</pre>
          </div>
        {:else}
          <p>포지션 없음</p>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  pre {
    background-color: #1a1a1a;
    padding: 1rem;
    border-radius: 0.5rem;
    overflow-x: auto;
  }
</style>