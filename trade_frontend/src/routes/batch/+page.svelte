<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { batchApi, type JobSchedule } from '$lib/api/batch.js';
  import IBKRCard from '$lib/components/IBKRCard.svelte';
  import IBKRButton from '$lib/components/IBKRButton.svelte';
  import IBKRBadge from '$lib/components/IBKRBadge.svelte';
  import IBKRTable from '$lib/components/IBKRTable.svelte';

  // 상태 관리
  let scheduledJobs: JobSchedule[] = [];
  let healthStatus: any = null;
  let marketStatus: any[] = [];
  let qualityReport: any = null;
  let failures: any[] = [];
  let loading = false;
  let error = '';
  let activeTab: 'jobs' | 'monitoring' | 'schedule' = 'jobs';

  // 실행 중인 작업 상태
  let runningJobs: Set<string> = new Set();

  async function loadData() {
    loading = true;
    error = '';
    try {
      // 병렬로 데이터 로드
      const [jobs, health, market, quality] = await Promise.all([
        batchApi.getScheduledJobs(),
        batchApi.getHealthStatus(),
        batchApi.getMarketStatus(),
        batchApi.getQualityReport()
      ]);

      scheduledJobs = jobs;
      healthStatus = health;
      marketStatus = market.markets || [];
      qualityReport = quality;

      // 실패 데이터는 별도로 로드
      await loadFailures();
    } catch (e) {
      error = '데이터를 불러오는데 실패했습니다.';
      console.error(e);
    } finally {
      loading = false;
    }
  }

  async function loadFailures() {
    try {
      const response = await batchApi.getFailures();
      failures = response.failures || [];
    } catch (e) {
      console.error('Failed to load failures:', e);
    }
  }

  async function runJob(jobName: string) {
    if (runningJobs.has(jobName)) return;
    
    runningJobs.add(jobName);
    runningJobs = new Set(runningJobs); // 반응성 트리거
    
    try {
      let result;
      switch (jobName) {
        case 'setInitStructureJob':
          result = await batchApi.initStructure();
          break;
        case 'addFutureMonthJob':
          result = await batchApi.addFutureMonth();
          break;
        case 'collectTypeDataJob':
          result = await batchApi.collectTypeData();
          break;
        case 'taskletJob':
          result = await batchApi.runTasklet();
          break;
        default:
          result = await batchApi.runJob(jobName);
      }
      
      // 성공 알림
      alert(`작업 실행 완료: ${result}`);
      
      // 데이터 새로고침
      await loadData();
    } catch (e) {
      alert(`작업 실행 실패: ${e}`);
      console.error(e);
    } finally {
      runningJobs.delete(jobName);
      runningJobs = new Set(runningJobs); // 반응성 트리거
    }
  }

  async function retryFailures() {
    if (confirm('실패한 작업들을 재시도하시겠습니까?')) {
      try {
        await batchApi.retryFailures();
        alert('재시도가 시작되었습니다.');
        await loadFailures();
      } catch (e) {
        alert('재시도 실행에 실패했습니다.');
        console.error(e);
      }
    }
  }

  function parseCronExpression(cron: string): string {
    // 간단한 cron 표현식 파싱
    const parts = cron.split(' ');
    if (parts.length !== 6) return cron;

    const [second, minute, hour, dayOfMonth, month, dayOfWeek] = parts;

    if (dayOfMonth === '1' && month === '1') {
      return `매월 1일 ${hour}시 ${minute}분`;
    } else if (dayOfMonth === '*') {
      if (hour === '*' && minute === '30') {
        return '매시 30분';
      } else if (minute === '*/10') {
        return '10분마다';
      }
      return `매일 ${hour}시 ${minute}분`;
    }
    return cron;
  }

  function getJobTypeIcon(jobName: string): string {
    if (jobName.includes('init')) return '🔧';
    if (jobName.includes('collect')) return '📊';
    if (jobName.includes('retry')) return '🔄';
    if (jobName.includes('quality')) return '📈';
    if (jobName.includes('future')) return '📅';
    return '⚙️';
  }

  onMount(() => {
    loadData();
    
    // 30초마다 상태 업데이트
    const interval = setInterval(loadData, 30000);
    
    return () => {
      clearInterval(interval);
    };
  });
</script>

<div class="p-6">
  <h1 class="text-3xl font-bold mb-6">배치 작업 관리</h1>

  {#if error}
    <div class="alert alert-error mb-4">
      <span>{error}</span>
    </div>
  {/if}

  <!-- 탭 메뉴 -->
  <div class="tabs tabs-boxed mb-6">
    <button 
      class="tab {activeTab === 'jobs' ? 'tab-active' : ''}"
      on:click={() => activeTab = 'jobs'}
    >
      작업 실행
    </button>
    <button 
      class="tab {activeTab === 'schedule' ? 'tab-active' : ''}"
      on:click={() => activeTab = 'schedule'}
    >
      스케줄 관리
    </button>
    <button 
      class="tab {activeTab === 'monitoring' ? 'tab-active' : ''}"
      on:click={() => activeTab = 'monitoring'}
    >
      모니터링
    </button>
  </div>

  {#if loading}
    <div class="flex justify-center p-8">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
  {:else}
    <!-- 작업 실행 탭 -->
    {#if activeTab === 'jobs'}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- 수동 실행 가능한 작업들 -->
        <IBKRCard>
          <h3 slot="title" class="text-lg font-semibold">
            {getJobTypeIcon('init')} 계약 구조 초기화
          </h3>
          <p class="text-sm text-base-content/70 mb-4">
            거래 가능한 계약의 구조를 초기화합니다.
          </p>
          <IBKRButton
            onClick={() => runJob('setInitStructureJob')}
            disabled={runningJobs.has('setInitStructureJob')}
            variant="primary"
            class="w-full"
          >
            {runningJobs.has('setInitStructureJob') ? '실행 중...' : '실행'}
          </IBKRButton>
        </IBKRCard>

        <IBKRCard>
          <h3 slot="title" class="text-lg font-semibold">
            {getJobTypeIcon('future')} 선물 월물 갱신
          </h3>
          <p class="text-sm text-base-content/70 mb-4">
            새로운 선물 월물을 추가합니다.
          </p>
          <IBKRButton
            onClick={() => runJob('addFutureMonthJob')}
            disabled={runningJobs.has('addFutureMonthJob')}
            variant="primary"
            class="w-full"
          >
            {runningJobs.has('addFutureMonthJob') ? '실행 중...' : '실행'}
          </IBKRButton>
        </IBKRCard>

        <IBKRCard>
          <h3 slot="title" class="text-lg font-semibold">
            {getJobTypeIcon('collect')} 데이터 수집
          </h3>
          <p class="text-sm text-base-content/70 mb-4">
            시장 데이터를 수집합니다.
          </p>
          <IBKRButton
            onClick={() => runJob('collectTypeDataJob')}
            disabled={runningJobs.has('collectTypeDataJob')}
            variant="primary"
            class="w-full"
          >
            {runningJobs.has('collectTypeDataJob') ? '실행 중...' : '실행'}
          </IBKRButton>
        </IBKRCard>
      </div>

      <!-- 시스템 상태 -->
      {#if healthStatus}
        <div class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="stat bg-base-200 rounded-lg">
            <div class="stat-title">전체 상태</div>
            <div class="stat-value text-2xl">
              <IBKRBadge variant={healthStatus.overall_status === 'HEALTHY' ? 'success' : 'error'}>
                {healthStatus.overall_status}
              </IBKRBadge>
            </div>
          </div>
          <div class="stat bg-base-200 rounded-lg">
            <div class="stat-title">활성 작업</div>
            <div class="stat-value text-2xl">{healthStatus.active_jobs || 0}</div>
          </div>
          <div class="stat bg-base-200 rounded-lg">
            <div class="stat-title">마지막 실행</div>
            <div class="stat-value text-lg">{healthStatus.last_run_time || 'N/A'}</div>
          </div>
        </div>
      {/if}
    {/if}

    <!-- 스케줄 관리 탭 -->
    {#if activeTab === 'schedule'}
      <IBKRCard>
        <h2 slot="title" class="text-xl font-semibold">예약된 작업</h2>
        <IBKRTable striped>
          <thead>
            <tr>
              <th>작업명</th>
              <th>설명</th>
              <th>실행 주기</th>
              <th>상태</th>
              <th>작업</th>
            </tr>
          </thead>
          <tbody>
            {#each scheduledJobs as job}
              <tr>
                <td class="font-mono text-sm">{job.jobName}</td>
                <td>{job.description}</td>
                <td class="text-sm">{parseCronExpression(job.cronExpression)}</td>
                <td>
                  <IBKRBadge variant={job.enabled ? 'success' : 'ghost'}>
                    {job.enabled ? '활성' : '비활성'}
                  </IBKRBadge>
                </td>
                <td>
                  <IBKRButton
                    onClick={() => runJob(job.jobName)}
                    disabled={runningJobs.has(job.jobName)}
                    variant="secondary"
                    size="sm"
                  >
                    수동 실행
                  </IBKRButton>
                </td>
              </tr>
            {/each}
          </tbody>
        </IBKRTable>
      </IBKRCard>
    {/if}

    <!-- 모니터링 탭 -->
    {#if activeTab === 'monitoring'}
      <div class="space-y-6">
        <!-- 품질 리포트 -->
        {#if qualityReport}
          <IBKRCard>
            <h3 slot="title" class="text-lg font-semibold">데이터 품질 리포트</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div class="text-center">
                <p class="text-sm text-base-content/70">완성도</p>
                <p class="text-2xl font-bold">{qualityReport.completionRate?.toFixed(1)}%</p>
              </div>
              <div class="text-center">
                <p class="text-sm text-base-content/70">총 심볼</p>
                <p class="text-2xl font-bold">{qualityReport.totalSymbols}</p>
              </div>
              <div class="text-center">
                <p class="text-sm text-base-content/70">누락 데이터</p>
                <p class="text-2xl font-bold text-error">{qualityReport.missingData}</p>
              </div>
              <div class="text-center">
                <p class="text-sm text-base-content/70">중복 데이터</p>
                <p class="text-2xl font-bold text-warning">{qualityReport.duplicates}</p>
              </div>
            </div>
          </IBKRCard>
        {/if}

        <!-- 실패 목록 -->
        <IBKRCard>
          <div slot="title" class="flex justify-between items-center">
            <h3 class="text-lg font-semibold">실패한 작업</h3>
            {#if failures.length > 0}
              <IBKRButton
                onClick={retryFailures}
                variant="warning"
                size="sm"
              >
                모두 재시도
              </IBKRButton>
            {/if}
          </div>
          
          {#if failures.length > 0}
            <IBKRTable>
              <thead>
                <tr>
                  <th>심볼</th>
                  <th>날짜</th>
                  <th>시도 횟수</th>
                  <th>에러</th>
                  <th>마지막 시도</th>
                </tr>
              </thead>
              <tbody>
                {#each failures.slice(0, 10) as failure}
                  <tr>
                    <td class="font-mono">{failure.symbol}</td>
                    <td>{failure.date}</td>
                    <td class="text-center">{failure.attempts}</td>
                    <td class="text-sm text-error">{failure.error}</td>
                    <td class="text-sm">{failure.lastAttempt}</td>
                  </tr>
                {/each}
              </tbody>
            </IBKRTable>
          {:else}
            <p class="text-center text-base-content/50 py-4">실패한 작업이 없습니다</p>
          {/if}
        </IBKRCard>

        <!-- 시장 상태 -->
        <IBKRCard>
          <h3 slot="title" class="text-lg font-semibold">시장 상태</h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            {#each marketStatus as market}
              <div class="p-4 bg-base-200 rounded-lg">
                <h4 class="font-semibold">{market.exchange}</h4>
                <p class="text-sm mt-2">
                  <IBKRBadge variant={market.isOpen ? 'success' : 'ghost'}>
                    {market.isOpen ? '열림' : '닫힘'}
                  </IBKRBadge>
                </p>
                {#if !market.isOpen && market.nextOpen}
                  <p class="text-xs text-base-content/70 mt-1">
                    다음 개장: {new Date(market.nextOpen).toLocaleString()}
                  </p>
                {/if}
              </div>
            {/each}
          </div>
        </IBKRCard>
      </div>
    {/if}
  {/if}
</div>