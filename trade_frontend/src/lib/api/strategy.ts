import { api } from './client';

export interface StrategyInfo {
  name: string;
  description: string;
  version: string;
  is_active: boolean;
  parameters: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface StrategyPerformance {
  strategy_name: string;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_profit: number;
  avg_loss: number;
  last_updated: string;
}

export interface StrategySignal {
  timestamp: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  reason: string;
}

export const strategyApi = {
  // 전략 목록 조회
  getStrategies: async (): Promise<StrategyInfo[]> => {
    const response = await api.get<StrategyInfo[]>('/api/strategy');
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 특정 전략 정보 조회
  getStrategy: async (name: string): Promise<StrategyInfo> => {
    const response = await api.get<StrategyInfo>(`/api/strategy/${name}`);
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 전략 성과 조회
  getStrategyPerformance: async (
    name: string,
    period: string = '1d'
  ): Promise<StrategyPerformance> => {
    const response = await api.get<StrategyPerformance>(`/api/strategy/${name}/performance?period=${period}`);
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 전략 활성화
  activateStrategy: async (name: string): Promise<void> => {
    const response = await api.post<void>(`/api/strategy/${name}/activate`, {});
    if (response.error) throw new Error(response.error);
  },

  // 전략 비활성화
  deactivateStrategy: async (name: string): Promise<void> => {
    const response = await api.post<void>(`/api/strategy/${name}/deactivate`, {});
    if (response.error) throw new Error(response.error);
  },

  // 전략 파라미터 업데이트
  updateStrategyParameters: async (
    name: string,
    parameters: Record<string, any>
  ): Promise<void> => {
    const response = await api.put<void>(`/api/strategy/${name}/parameters`, parameters);
    if (response.error) throw new Error(response.error);
  },

  // 전략 신호 이력 조회
  getStrategySignals: async (
    name: string,
    limit: number = 100
  ): Promise<{ strategy: string; signals: StrategySignal[]; count: number }> => {
    const response = await api.get<{ strategy: string; signals: StrategySignal[]; count: number }>(`/api/strategy/${name}/signals?limit=${limit}`);
    if (response.error) throw new Error(response.error);
    return response.data!;
  }
};