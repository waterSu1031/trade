import { browser } from '$app/environment';
import { errorStore } from '$lib/stores/error';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        }
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMessage = data.detail || data.message || `API Error: ${response.status}`;
        if (browser) {
          errorStore.addError(errorMessage, 'error');
        }
        return {
          error: errorMessage,
          status: response.status
        };
      }

      return {
        data,
        status: response.status
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Network error';
      if (browser) {
        errorStore.addError(`Failed to connect to ${endpoint}: ${errorMessage}`, 'error');
      }
      return {
        error: errorMessage,
        status: 0
      };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  }

  async put<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body)
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const api = new ApiClient(API_URL);