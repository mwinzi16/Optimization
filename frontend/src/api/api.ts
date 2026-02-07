import type {
  ApiEnvelope,
  AssetInfo,
  EfficientFrontierPoint,
  HealthResponse,
  OptimizationRequest,
  OptimizationResponse,
  UploadResponse,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE ?? '';
const API_PREFIX = `${BASE_URL}/api/v1`;

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  url: string,
  options: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60_000);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const body = (await response.json()) as ApiEnvelope<T>;

    if (!response.ok) {
      const err = body.errors?.[0];
      throw new ApiError(
        err?.message ?? response.statusText,
        response.status,
        err?.code,
        err?.details,
      );
    }

    return body.data;
  } finally {
    clearTimeout(timeout);
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>(`${API_PREFIX}/health`);
}

export async function fetchAssets(): Promise<AssetInfo[]> {
  return request<AssetInfo[]>(`${API_PREFIX}/assets`);
}

export async function optimizePortfolio(
  params: OptimizationRequest,
): Promise<OptimizationResponse> {
  return request<OptimizationResponse>(`${API_PREFIX}/optimize`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getEfficientFrontier(params: {
  min_weight?: number;
  max_weight?: number;
  n_points?: number;
  risk_free_rate?: number;
}): Promise<EfficientFrontierPoint[]> {
  const query = new URLSearchParams();
  if (params.min_weight != null) query.set('min_weight', String(params.min_weight));
  if (params.max_weight != null) query.set('max_weight', String(params.max_weight));
  if (params.n_points != null) query.set('n_points', String(params.n_points));
  if (params.risk_free_rate != null) query.set('risk_free_rate', String(params.risk_free_rate));
  return request<EfficientFrontierPoint[]>(`${API_PREFIX}/efficient-frontier?${query}`);
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120_000);

  try {
    const response = await fetch(`${API_PREFIX}/upload`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    const body = (await response.json()) as ApiEnvelope<UploadResponse>;

    if (!response.ok) {
      const err = body.errors?.[0];
      throw new ApiError(
        err?.message ?? 'Upload failed',
        response.status,
        err?.code,
      );
    }

    return body.data;
  } finally {
    clearTimeout(timeout);
  }
}

export async function resetData(): Promise<{ status: string; message: string }> {
  return request<{ status: string; message: string }>(`${API_PREFIX}/reset`, {
    method: 'POST',
  });
}