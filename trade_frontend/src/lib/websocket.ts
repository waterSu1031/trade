/**
 * WebSocket client for real-time data streaming
 */

export interface WebSocketMessage {
  type: string;
  data?: any;
  topic?: string;
  timestamp?: number;
}

export interface PriceUpdate {
  type: 'price_update';
  timestamp: string;
  data: Record<string, number>;
}

export interface PositionUpdate {
  type: 'position_update';
  timestamp: string;
  data: Array<{
    symbol: string;
    qty: number;
    avg_price: number;
    current_price: number;
    unrealized_pnl: number;
    pnl_percent: number;
    market_value: number;
  }>;
}

export interface Alert {
  type: 'alert';
  data: {
    id: string;
    type: string;
    severity: 'info' | 'warning' | 'critical';
    symbol?: string;
    message: string;
    timestamp: string;
  };
}

export class RealtimeWebSocket {
  private ws: WebSocket | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private subscriptions: Set<string> = new Set();
  private messageHandlers: Map<string, Array<(data: any) => void>> = new Map();
  private connectionPromise: Promise<void> | null = null;
  
  constructor(private url: string = 'ws://localhost:8000/api/ws/ws') {}
  
  async connect(): Promise<void> {
    if (this.connectionPromise) {
      return this.connectionPromise;
    }
    
    this.connectionPromise = new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.setupPingInterval();
          this.resubscribeTopics();
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
        
        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.cleanup();
          this.scheduleReconnect();
        };
      } catch (error) {
        reject(error);
      }
    });
    
    return this.connectionPromise;
  }
  
  private handleMessage(message: WebSocketMessage) {
    const handlers = this.messageHandlers.get(message.type) || [];
    handlers.forEach(handler => handler(message));
  }
  
  subscribe(topic: string): void {
    this.subscriptions.add(topic);
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        topic
      }));
    }
  }
  
  unsubscribe(topic: string): void {
    this.subscriptions.delete(topic);
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        topic
      }));
    }
  }
  
  on(messageType: string, handler: (data: any) => void): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }
  
  off(messageType: string, handler: (data: any) => void): void {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index !== -1) {
        handlers.splice(index, 1);
      }
    }
  }
  
  private setupPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'ping',
          timestamp: Date.now()
        }));
      }
    }, 30000); // Ping every 30 seconds
  }
  
  private resubscribeTopics(): void {
    this.subscriptions.forEach(topic => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'subscribe',
          topic
        }));
      }
    });
  }
  
  private cleanup(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    this.connectionPromise = null;
  }
  
  private scheduleReconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    
    this.reconnectTimeout = setTimeout(() => {
      console.log('Attempting to reconnect WebSocket...');
      this.connect();
    }, 5000); // Reconnect after 5 seconds
  }
  
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    
    this.cleanup();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const realtimeWS = new RealtimeWebSocket();