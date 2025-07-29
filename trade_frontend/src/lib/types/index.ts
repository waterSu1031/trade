// 자동매매 관련 타입 정의

export interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  price: number;
  timestamp: Date;
  status: 'pending' | 'filled' | 'cancelled';
  profit?: number;
}

export interface TradingStatus {
  isRunning: boolean;
  totalProfit: number;
  todayProfit: number;
  tradeCount: number;
  winRate: number;
}

export interface BacktestResult {
  id: string;
  name: string;
  startDate: Date;
  endDate: Date;
  totalReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  trades: Trade[];
}

export interface BatchJob {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime?: Date;
  endTime?: Date;
  logs: string[];
}

export interface Statistics {
  dailyProfits: { date: string; profit: number }[];
  monthlyStats: { month: string; trades: number; profit: number }[];
  symbolStats: { symbol: string; trades: number; profit: number; winRate: number }[];
}