import type { NationalSummaryResponse, WatchlistResponse, PipelineLastRun } from '../types/api';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        url.searchParams.append(key, String(val));
      }
    });
  }

  const response = await fetch(url.toString(), {
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new ApiError(response.status, `API request failed with status ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchNationalSummary(month?: string): Promise<NationalSummaryResponse> {
  return request<NationalSummaryResponse>('/national/summary', { report_month: month });
}

export async function fetchWatchlist(params?: {
  report_month?: string;
  regime?: string;
  sector?: string;
  ministry?: string;
  min_strength?: number;
}): Promise<WatchlistResponse> {
  return request<WatchlistResponse>('/watchlist', params);
}

export async function fetchPipelineLastRun(): Promise<PipelineLastRun> {
  return request<PipelineLastRun>('/pipeline/last-run');
}
