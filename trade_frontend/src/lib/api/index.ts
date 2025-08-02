export * from './client';
export * from './trades';
export * from './positions';
export * from './statistics';
export * from './strategy';
export * from './trading';
export * from './dashboard';

// Simple WebSocket manager stub for build compatibility
export const wsManager = {
  connect: () => console.log('WebSocket connecting...'),
  subscribe: (topic: string, callback: (data: any) => void) => console.log(`Subscribed to ${topic}`),
  disconnect: () => console.log('WebSocket disconnecting...')
};

// batch API는 axios 의존성 때문에 필요한 곳에서 직접 import