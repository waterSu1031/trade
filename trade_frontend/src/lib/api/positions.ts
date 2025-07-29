import { api } from './client';

export interface Position {
  id: number;
  symbol: string;
  quantity: number;
  average_cost: number;
  market_price: number;
  market_value: number;
  unrealized_pnl: number;
  realized_pnl: number;
  currency: string;
  exchange: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PositionCreate {
  symbol: string;
  quantity: number;
  average_cost: number;
  market_price?: number;
  market_value?: number;
  unrealized_pnl?: number;
  realized_pnl?: number;
  currency?: string;
  exchange?: string;
  is_active?: boolean;
}

export interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  total_unrealized_pnl: number;
  total_realized_pnl: number;
  position_count: number;
  currency: string;
}

export const positionsApi = {
  // Get all positions
  async getPositions(activeOnly = true, skip = 0, limit = 100) {
    return api.get<Position[]>(
      `/api/positions/?active_only=${activeOnly}&skip=${skip}&limit=${limit}`
    );
  },

  // Get position by ID
  async getPosition(positionId: number) {
    return api.get<Position>(`/api/positions/${positionId}`);
  },

  // Create new position
  async createPosition(position: PositionCreate) {
    return api.post<Position>('/api/positions/', position);
  },

  // Update position
  async updatePosition(positionId: number, position: Partial<PositionCreate>) {
    return api.put<Position>(`/api/positions/${positionId}`, position);
  },

  // Get current positions from IBKR
  async getCurrentPositions() {
    return api.get<Position[]>('/api/positions/live/current');
  },

  // Get portfolio summary
  async getPortfolioSummary() {
    return api.get<PortfolioSummary>('/api/positions/portfolio/summary');
  },

  // Sync positions with IBKR
  async syncPositions() {
    return api.post<{ message: string; synced_count: number }>('/api/positions/sync', {});
  }
};