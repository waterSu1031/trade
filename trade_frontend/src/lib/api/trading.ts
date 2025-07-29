import { api } from './client';

export type TradingMode = 'live' | 'paper' | 'backtest';
export type TradingStatus = 'idle' | 'running' | 'paused' | 'stopped' | 'error';
export type OrderType = 'MKT' | 'LMT' | 'STP' | 'STP_LMT';
export type OrderSide = 'BUY' | 'SELL';
export type OrderStatus = 'pending' | 'submitted' | 'filled' | 'cancelled' | 'rejected';

export interface TradingSystemStatus {
  mode: TradingMode;
  status: TradingStatus;
  active_strategies: string[];
  ibkr_connected: boolean;
  last_heartbeat: string;
  uptime_seconds: number;
  total_positions: number;
  total_orders_today: number;
}

export interface AccountInfo {
  account_id: string;
  total_cash: number;
  net_liquidation: number;
  buying_power: number;
  total_positions_value: number;
  total_pnl: number;
  daily_pnl: number;
  margin_used: number;
  margin_available: number;
  currency: string;
  last_updated: string;
}

export interface OrderRequest {
  symbol: string;
  side: OrderSide;
  quantity: number;
  order_type: OrderType;
  limit_price?: number;
  stop_price?: number;
  time_in_force?: string;
  strategy_name?: string;
}

export interface OrderResponse {
  order_id: string;
  symbol: string;
  side: OrderSide;
  quantity: number;
  order_type: OrderType;
  status: OrderStatus;
  submitted_at: string;
  filled_at?: string;
  avg_fill_price?: number;
  commission?: number;
}

export const tradingApi = {
  // 시스템 상태 조회
  getStatus: async (): Promise<TradingSystemStatus> => {
    const response = await api.get<TradingSystemStatus>('/api/trading/status');
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 트레이딩 시작
  startTrading: async (mode: TradingMode = 'paper'): Promise<any> => {
    const response = await api.post<any>(`/api/trading/start?mode=${mode}`, {});
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 트레이딩 중지
  stopTrading: async (): Promise<any> => {
    const response = await api.post<any>('/api/trading/stop', {});
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 트레이딩 일시정지
  pauseTrading: async (): Promise<any> => {
    const response = await api.post<any>('/api/trading/pause', {});
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 트레이딩 재개
  resumeTrading: async (): Promise<any> => {
    const response = await api.post<any>('/api/trading/resume', {});
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 계좌 정보 조회
  getAccountInfo: async (): Promise<AccountInfo> => {
    const response = await api.get<AccountInfo>('/api/trading/account');
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 주문 실행
  placeOrder: async (order: OrderRequest): Promise<OrderResponse> => {
    const response = await api.post<OrderResponse>('/api/trading/orders', order);
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 주문 목록 조회
  getOrders: async (params?: {
    status?: OrderStatus;
    symbol?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<OrderResponse[]> => {
    const queryParams = new URLSearchParams();
    if (params?.status) queryParams.append('status', params.status);
    if (params?.symbol) queryParams.append('symbol', params.symbol);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    
    const response = await api.get<OrderResponse[]>(`/api/trading/orders?${queryParams}`);
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 주문 취소
  cancelOrder: async (orderId: string): Promise<any> => {
    const response = await api.delete<any>(`/api/trading/orders/${orderId}`);
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 모든 주문 취소
  cancelAllOrders: async (): Promise<any> => {
    const response = await api.post<any>('/api/trading/orders/cancel-all', {});
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 모든 포지션 청산
  closeAllPositions: async (): Promise<any> => {
    const response = await api.post<any>('/api/trading/positions/close-all', {});
    if (response.error) throw new Error(response.error);
    return response.data!;
  },

  // 일별 손익 조회
  getDailyPnL: async (days: number = 30): Promise<any> => {
    const response = await api.get<any>(`/api/trading/pnl/daily?days=${days}`);
    if (response.error) throw new Error(response.error);
    return response.data!;
  }
};