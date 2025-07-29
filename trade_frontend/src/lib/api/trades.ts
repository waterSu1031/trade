import { api } from './client';

export interface Trade {
  id: number;
  order_id: string;
  symbol: string;
  action: string;
  quantity: number;
  price: number;
  commission: number;
  realized_pnl: number;
  status: string;
  exchange: string;
  currency: string;
  execution_time: string;
  created_at: string;
  updated_at: string;
}

export interface TradeCreate {
  order_id: string;
  symbol: string;
  action: string;
  quantity: number;
  price: number;
  commission?: number;
  realized_pnl?: number;
  status?: string;
  exchange?: string;
  currency?: string;
  execution_time?: string;
}

export interface DailySummary {
  date: string;
  total_trades: number;
  total_volume: number;
  total_pnl: number;
  total_commission: number;
  net_pnl: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
}

export const tradesApi = {
  // Get all trades
  async getTrades(skip = 0, limit = 100) {
    return api.get<Trade[]>(`/api/trades/?skip=${skip}&limit=${limit}`);
  },

  // Get trade by ID
  async getTrade(tradeId: number) {
    return api.get<Trade>(`/api/trades/${tradeId}`);
  },

  // Create new trade
  async createTrade(trade: TradeCreate) {
    return api.post<Trade>('/api/trades/', trade);
  },

  // Update trade
  async updateTrade(tradeId: number, trade: Partial<TradeCreate>) {
    return api.put<Trade>(`/api/trades/${tradeId}`, trade);
  },

  // Get recent trades from IBKR
  async getRecentTrades(days = 1) {
    return api.get<Trade[]>(`/api/trades/live/recent?days=${days}`);
  },

  // Get daily summary
  async getDailySummary(startDate?: string, endDate?: string) {
    let url = '/api/trades/summary/daily';
    const params = new URLSearchParams();
    
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    return api.get<DailySummary[]>(url);
  }
};