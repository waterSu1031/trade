import { writable } from 'svelte/store';

export interface ErrorInfo {
  message: string;
  type: 'error' | 'warning' | 'info';
  timestamp: Date;
  id: string;
}

function createErrorStore() {
  const { subscribe, set, update } = writable<ErrorInfo[]>([]);

  return {
    subscribe,
    addError: (message: string, type: 'error' | 'warning' | 'info' = 'error') => {
      const error: ErrorInfo = {
        message,
        type,
        timestamp: new Date(),
        id: `${Date.now()}-${Math.random()}`
      };
      
      update(errors => [...errors, error]);
      
      // Auto-remove after 5 seconds
      setTimeout(() => {
        update(errors => errors.filter(e => e.id !== error.id));
      }, 5000);
    },
    removeError: (id: string) => {
      update(errors => errors.filter(e => e.id !== id));
    },
    clearAll: () => set([])
  };
}

export const errorStore = createErrorStore();