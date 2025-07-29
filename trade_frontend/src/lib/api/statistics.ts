import { api } from './client';

export interface DailyStats {
  date: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  total_pnl: number;
  average_win: number;
  average_loss: number;
  win_rate: number;
  profit_factor: number;
  sharpe_ratio: number;
}

export interface OverallStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  average_pnl: number;
  max_win: number;
  max_loss: number;
  profit_factor: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  avg_holding_time: number;
  best_symbol: string;
  worst_symbol: string;
}

export interface AccountSummary {
  net_liquidation: number;
  total_cash_value: number;
  total_positions_value: number;
  buying_power: number;
  excess_liquidity: number;
  maintenance_margin: number;
  initial_margin: number;
  currency: string;
  updated_at: string;
}

export interface PerformanceMetrics {
  daily_returns: number[];
  cumulative_returns: number[];
  drawdown_series: number[];
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  max_drawdown: number;
  max_drawdown_duration: number;
  volatility: number;
  downside_deviation: number;
  value_at_risk: number;
  expected_shortfall: number;
}

export interface SymbolStats {
  symbol: string;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  average_pnl: number;
  total_volume: number;
  total_commission: number;
  net_pnl: number;
}

export const statisticsApi = {
  // Get daily statistics
  async getDailyStats(startDate?: string, endDate?: string) {
    let url = '/api/statistics/daily';
    const params = new URLSearchParams();
    
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    return api.get<DailyStats[]>(url);
  },

  // Get overall statistics
  async getOverallStats() {
    return api.get<OverallStats>('/api/statistics/overall');
  },

  // Get account summary
  async getAccountSummary() {
    return api.get<AccountSummary>('/api/statistics/account');
  },

  // Get performance metrics
  async getPerformanceMetrics(days = 30) {
    return api.get<PerformanceMetrics>(`/api/statistics/performance?days=${days}`);
  },

  // Get statistics by symbol
  async getSymbolStats(symbol: string) {
    return api.get<SymbolStats>(`/api/statistics/symbols/${symbol}`);
  }
};