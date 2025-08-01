/**
 * TypeScript 모델 정의 (Frontend용)
 * 공통 모델과 일치하도록 생성
 */

// Enums
export enum SecType {
  STK = "STK",
  FUT = "FUT",
  OPT = "OPT",
  CASH = "CASH",
  IND = "IND",
  CFD = "CFD",
  BOND = "BOND",
  FUND = "FUND",
  CMDTY = "CMDTY"
}

export enum OrderAction {
  BUY = "BUY",
  SELL = "SELL"
}

export enum OrderType {
  MKT = "MKT",
  LMT = "LMT",
  STP = "STP",
  STP_LMT = "STP_LMT"
}

export enum OrderStatus {
  PendingSubmit = "PendingSubmit",
  PreSubmitted = "PreSubmitted",
  Submitted = "Submitted",
  Filled = "Filled",
  Cancelled = "Cancelled",
  Inactive = "Inactive"
}

export enum RightType {
  C = "C",
  P = "P"
}

// Interfaces
export interface Contract {
  conId: number;
  symbol: string;
  secType: SecType;
  exchange: string;
  currency: string;
  
  // Optional fields
  lastTradeDateOrContractMonth?: string;
  strike?: number;
  rightType?: RightType;
  multiplier?: string;
  primaryExchange?: string;
  localSymbol?: string;
  tradingClass?: string;
  description?: string;
}

export interface Order {
  orderId: string;
  symbol: string;
  action: OrderAction;
  orderType: OrderType;
  totalQuantity: number;
  
  // Optional fields
  clientId?: number;
  permId?: number;
  parentId?: string;
  secType?: SecType;
  exchange?: string;
  lmtPrice?: number;
  auxPrice?: number;
  tif?: string;
  account?: string;
  status?: OrderStatus;
  filled?: number;
  remaining?: number;
  avgFillPrice?: number;
}

export interface Position {
  symbol: string;
  quantity: number;
  avgCost: number;
  
  // Optional fields
  conId?: number;
  secType?: SecType;
  exchange?: string;
  currency?: string;
  marketPrice?: number;
  marketValue?: number;
  unrealizedPnl?: number;
  realizedPnl?: number;
  account?: string;
}

export interface TradeEvent {
  execId: string;
  orderId: string;
  time: string; // ISO string
  symbol: string;
  side: string;
  shares: number;
  price: number;
  
  // Optional fields
  clientId?: number;
  permId?: number;
  acctNumber?: string;
  secType?: SecType;
  exchange?: string;
  position?: number;
  avgCost?: number;
  realizedPnl?: number;
  commission?: number;
}

// Utility functions
export function toSnakeCase(obj: Record<string, any>): Record<string, any> {
  const snakeCaseObj: Record<string, any> = {};
  
  for (const [key, value] of Object.entries(obj)) {
    const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    snakeCaseObj[snakeKey] = value;
  }
  
  return snakeCaseObj;
}

export function toCamelCase(obj: Record<string, any>): Record<string, any> {
  const camelCaseObj: Record<string, any> = {};
  
  for (const [key, value] of Object.entries(obj)) {
    const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
    camelCaseObj[camelKey] = value;
  }
  
  return camelCaseObj;
}