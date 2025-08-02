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

  // 스케줄 관리 - 백엔드에서 실제 스케줄 정보 조회
  getScheduledJobs: async (): Promise<JobSchedule[]> => {
    const response = await batchApiClient.get('/api/batch/scheduled-jobs');
    return response.data;
  },
  
  // 거래시간 업데이트
  updateTradingHours: async (): Promise<any> => {
    const response = await batchApiClient.post('/api/batch/update-trading-hours');
    return response.data;
  }
};