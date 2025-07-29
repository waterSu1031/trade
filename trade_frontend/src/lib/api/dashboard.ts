import { api } from './client';

export type TimeRange = '1d' | '1w' | '1m' | '3m' | '6m' | '1y' | 'all';

export interface DashboardSummary {
  total_equity: number;
  daily_pnl: number;
  daily_pnl_percent: number;
  weekly_pnl: number;
  weekly_pnl_percent: number;
  monthly_pnl: number;
  monthly_pnl_percent: number;
  total_positions: number;
  active_strategies: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown: number;
  last_updated: string;
}

export interface PerformanceMetrics {
  date: string;
  equity: number;
  daily_return: number;
  cumulative_return: number;
  drawdown: number;
  volume: number;
  trades: number;
}

export interface TopPerformer {
  name: string;
  type: 'stock' | 'strategy';
  pnl: number;
  pnl_percent: number;
  trades: number;
}

export interface MarketOverview {
  spy_price: number;
  spy_change: number;
  spy_change_percent: number;
  vix_level: number;
  vix_change: number;
  market_sentiment: 'bullish' | 'neutral' | 'bearish';
}

export interface AlertInfo {
  id: string;
  type: 'risk' | 'opportunity' | 'system';
  severity: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: string;
  is_read: boolean;
}

export interface Activity {
  timestamp: string;
  type: string;
  description: string;
  strategy?: string;
}

export interface RiskMetrics {
  var_95: number;
  var_99: number;
  beta: number;
  correlation_spy: number;
  position_concentration: number;
  leverage: number;
  margin_usage: number;
}

export const dashboardApi = {
  // 대시보드 요약 조회
  getSummary: async (): Promise<DashboardSummary> => {
    const response = await api.get<DashboardSummary>('/api/dashboard/summary');
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 성과 이력 조회
  getPerformance: async (
    range: TimeRange = '1m',
    resolution: string = 'daily'
  ): Promise<PerformanceMetrics[]> => {
    const response = await api.get<PerformanceMetrics[]>(`/api/dashboard/performance?range=${range}&resolution=${resolution}`);
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 상위 성과자 조회
  getTopPerformers: async (
    type?: 'stock' | 'strategy',
    limit: number = 5
  ): Promise<TopPerformer[]> => {
    let url = `/api/dashboard/top-performers?limit=${limit}`;
    if (type) url += `&type=${type}`;
    const response = await api.get<TopPerformer[]>(url);
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 시장 개요 조회
  getMarketOverview: async (): Promise<MarketOverview> => {
    const response = await api.get<MarketOverview>('/api/dashboard/market-overview');
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 알림 목록 조회
  getAlerts: async (
    unreadOnly: boolean = false,
    limit: number = 10
  ): Promise<AlertInfo[]> => {
    const response = await api.get<AlertInfo[]>(`/api/dashboard/alerts?unread_only=${unreadOnly}&limit=${limit}`);
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 알림 읽음 표시
  markAlertRead: async (alertId: string): Promise<void> => {
    const response = await api.put<void>(`/api/dashboard/alerts/${alertId}/read`, {});
    if (response.error) throw new Error(response.error);
  },

  // 활동 피드 조회
  getActivityFeed: async (limit: number = 20): Promise<{ activities: Activity[]; count: number }> => {
    const response = await api.get<{ activities: Activity[]; count: number }>(`/api/dashboard/activity-feed?limit=${limit}`);
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 리스크 지표 조회
  getRiskMetrics: async (): Promise<RiskMetrics> => {
    const response = await api.get<RiskMetrics>('/api/dashboard/risk-metrics');
    if (response.error) throw new Error(response.error);
    return response.data!;
  }
};