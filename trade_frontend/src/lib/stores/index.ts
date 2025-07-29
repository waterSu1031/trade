import { writable } from 'svelte/store';
import type { Trade, TradingStatus, BacktestResult, BatchJob } from '$lib/types';

// 매매 상태 스토어
export const tradingStatus = writable<TradingStatus>({
  isRunning: false,
  totalProfit: 0,
  todayProfit: 0,
  tradeCount: 0,
  winRate: 0
});

// 거래 내역 스토어
export const trades = writable<Trade[]>([]);

// 백테스트 결과 스토어
export const backtestResults = writable<BacktestResult[]>([]);

// 배치 작업 스토어
export const batchJobs = writable<BatchJob[]>([]);

// 테마 스토어
export const currentTheme = writable<string>('corporate');

// WebSocket 연결 상태
export const wsConnected = writable<boolean>(false);