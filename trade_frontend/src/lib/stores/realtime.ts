/**
 * Svelte stores for real-time data management
 */
import { writable, derived } from 'svelte/store';
import { realtimeWS, type PriceUpdate, type PositionUpdate, type Alert } from '$lib/websocket';

// Price data store
export const priceData = writable<Record<string, number>>({});

// Position data store  
export const positionData = writable<Array<{
  symbol: string;
  qty: number;
  avg_price: number;
  current_price: number;
  unrealized_pnl: number;
  pnl_percent: number;
  market_value: number;
}>>([]);

// Alerts store
export const alerts = writable<Alert['data'][]>([]);

// Connection status
export const wsConnected = writable(false);

// Derived store for total portfolio value
export const totalPortfolioValue = derived(positionData, ($positions) => {
  return $positions.reduce((total, pos) => total + pos.market_value, 0);
});

// Derived store for total P&L
export const totalPnL = derived(positionData, ($positions) => {
  return $positions.reduce((total, pos) => total + pos.unrealized_pnl, 0);
});

// Initialize WebSocket connection and subscriptions
export async function initializeRealtime() {
  try {
    // Connect to WebSocket
    await realtimeWS.connect();
    wsConnected.set(true);
    
    // Subscribe to topics
    realtimeWS.subscribe('price_updates');
    realtimeWS.subscribe('position_updates');
    realtimeWS.subscribe('alerts');
    
    // Handle price updates
    realtimeWS.on('price_update', (message: PriceUpdate) => {
      priceData.set(message.data);
    });
    
    // Handle position updates
    realtimeWS.on('position_update', (message: PositionUpdate) => {
      positionData.set(message.data);
    });
    
    // Handle alerts
    realtimeWS.on('alert', (message: Alert) => {
      alerts.update(currentAlerts => {
        // Keep only last 50 alerts
        const newAlerts = [message.data, ...currentAlerts].slice(0, 50);
        return newAlerts;
      });
    });
    
    // Handle connection status
    realtimeWS.on('subscription_confirmed', (message) => {
      console.log(`Subscribed to ${message.topic}`);
    });
    
  } catch (error) {
    console.error('Failed to initialize realtime connection:', error);
    wsConnected.set(false);
  }
}

// Cleanup function
export function cleanupRealtime() {
  realtimeWS.disconnect();
  wsConnected.set(false);
}

// Helper function to format price
export function formatPrice(price: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(price);
}

// Helper function to format percentage
export function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

// Alert severity colors
export const alertColors = {
  info: 'text-ibkr-info',
  warning: 'text-ibkr-warning',
  critical: 'text-ibkr-danger'
};