import axios, { AxiosInstance } from 'axios';

// Batch API용 별도 axios 인스턴스 생성
const batchApiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_BATCH_API_URL || 'http://localhost:8080',
  headers: {
    'Content-Type': 'application/json'
  }
});

export interface BatchJob {
  id: string;
  name: string;
  description?: string;
  status: 'running' | 'completed' | 'failed' | 'scheduled';
  progress?: number;
  startTime?: string;
  endTime?: string;
  nextRunTime?: string;
  cronExpression?: string;
  logs?: string[];
  error?: string;
}

export interface JobSchedule {
  jobName: string;
  description: string;
  cronExpression: string;
  enabled: boolean;
  lastRun?: string;
  nextRun?: string;
}

export interface DataCollectionStatus {
  symbol: string;
  date: string;
  status: string;
  attempts: number;
  error?: string;
  lastAttempt?: string;
}

export interface MarketHealth {
  exchange: string;
  isOpen: boolean;
  nextOpen?: string;
  nextClose?: string;
  status: string;
}

export const batchApi = {
  // Job 실행 관련
  runJob: async (jobName: string): Promise<string> => {
    const response = await batchApiClient.get(`/api/batch/run-job/${jobName}`);
    return response.data;
  },

  initStructure: async (): Promise<string> => {
    const response = await batchApiClient.get('/api/batch/init-structure');
    return response.data;
  },

  addFutureMonth: async (): Promise<string> => {
    const response = await batchApiClient.post('/api/batch/add-future-month');
    return response.data;
  },

  collectTypeData: async (): Promise<string> => {
    const response = await batchApiClient.post('/api/batch/collect-type-data');
    return response.data;
  },

  runTasklet: async (): Promise<string> => {
    const response = await batchApiClient.post('/api/batch/tasklet');
    return response.data;
  },

  // 모니터링 관련
  getHealthStatus: async (): Promise<any> => {
    const response = await batchApiClient.get('/api/monitoring/health');
    return response.data;
  },

  getFailures: async (symbol?: string, startDate?: string, endDate?: string): Promise<any> => {
    const params = new URLSearchParams();
    if (symbol) params.append('symbol', symbol);
    if (startDate) params.append('startDate', startDate);
    if (endDate) params.append('endDate', endDate);
    
    const response = await batchApiClient.get(`/api/monitoring/failures?${params}`);
    return response.data;
  },

  getQualityReport: async (date?: string): Promise<any> => {
    const params = date ? `?date=${date}` : '';
    const response = await batchApiClient.get(`/api/monitoring/quality-report${params}`);
    return response.data;
  },

  getMarketStatus: async (exchange?: string): Promise<any> => {
    const params = exchange ? `?exchange=${exchange}` : '';
    const response = await batchApiClient.get(`/api/monitoring/market-status${params}`);
    return response.data;
  },

  retryFailures: async (symbol?: string, date?: string): Promise<any> => {
    const params = new URLSearchParams();
    if (symbol) params.append('symbol', symbol);
    if (date) params.append('date', date);
    
    const response = await batchApiClient.post(`/api/monitoring/retry-failures?${params}`);
    return response.data;
  },

  getCollectionSchedule: async (): Promise<any> => {
    const response = await batchApiClient.get('/api/monitoring/collection-schedule');
    return response.data;
  },

  // 스케줄 관리 (프론트엔드에서 표시용)
  getScheduledJobs: async (): Promise<JobSchedule[]> => {
    // 스케줄 정보는 BatchScheduler.java에 하드코딩되어 있으므로
    // 프론트엔드에서 정의하여 표시
    return [
      {
        jobName: 'setInitStructureJob',
        description: '계약 구조 초기화',
        cronExpression: '0 0 1 * * ?',
        enabled: true
      },
      {
        jobName: 'addFutureMonthJob',
        description: '선물 월물 갱신',
        cronExpression: '0 0 1 1 * ?',
        enabled: true
      },
      {
        jobName: 'collectTypeDataJob-US',
        description: '미국 시장 데이터 수집',
        cronExpression: '0 0 6 * * ?',
        enabled: true
      },
      {
        jobName: 'collectTypeDataJob-EU',
        description: '유럽 시장 데이터 수집',
        cronExpression: '0 0 2 * * ?',
        enabled: true
      },
      {
        jobName: 'collectTypeDataJob-ASIA',
        description: '아시아 시장 데이터 수집',
        cronExpression: '0 30 16 * * ?',
        enabled: true
      },
      {
        jobName: 'retryFailedCollections',
        description: '실패 데이터 재시도',
        cronExpression: '0 30 * * * ?',
        enabled: true
      },
      {
        jobName: 'dailyQualityReport',
        description: '일일 품질 리포트',
        cronExpression: '0 0 8 * * ?',
        enabled: true
      }
    ];
  }
};