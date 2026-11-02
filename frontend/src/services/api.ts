/**
 * API client service for communicating with FACECORE AI backend.
 */

import type {
  HealthResponse,
  EngineMetadata,
  ImageValidationResponse,
  ComparisonResponse,
  DatasetMetadata,
  BenchmarkRunSummary,
  BenchmarkResult,
  BenchmarkRunConfig,
  DashboardStatsResponse,
  ComparisonHistoryRecord,
  ReadinessResponse,
} from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001').replace(/\/$/, '');

export class ApiError extends Error {
  status?: number;
  details?: unknown;

  constructor(message: string, status?: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Perform health check against backend service.
 */
export async function fetchHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new ApiError(`Health check failed with status ${res.status}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      'Backend service unavailable. Please ensure the Python FastAPI backend is running on ' + API_BASE_URL
    );
  }
}

/**
 * Retrieve metadata for the currently active engine.
 */
export async function fetchEngineInfo(): Promise<EngineMetadata> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/engine-info`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new ApiError(`Engine metadata request failed with status ${res.status}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Unable to fetch inference engine information.');
  }
}

/**
 * Options for facial comparison API submission.
 */
export interface CompareOptions {
  selectedFaceA?: number | null;
  selectedFaceB?: number | null;
  cropBoxA?: [number, number, number, number] | null;
  cropBoxB?: [number, number, number, number] | null;
  thresholdProfile?: string;
  customThreshold?: number;
  signal?: AbortSignal;
}

/**
 * Validate an image file through backend security and quality diagnostics, with optional manual crop.
 */
export async function validateImageApi(
  file: File,
  cropBox?: [number, number, number, number] | null
): Promise<ImageValidationResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (cropBox) {
      formData.append('crop_box', JSON.stringify(cropBox));
    }

    const res = await fetch(`${API_BASE_URL}/api/validate-image`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({ detail: res.statusText }));
      throw new ApiError(errBody.detail || `Validation failed with status ${res.status}`, res.status);
    }

    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      'Network error connecting to validation endpoint. Verify backend is running.'
    );
  }
}

/**
 * Submit two validated images for facial comparison evaluation with optional face selection and cropping.
 */
export async function compareImagesApi(
  fileA: File,
  fileB: File,
  optionsOrSignal?: AbortSignal | CompareOptions
): Promise<ComparisonResponse> {
  try {
    const formData = new FormData();
    formData.append('image_a', fileA);
    formData.append('image_b', fileB);

    let signal: AbortSignal | undefined;
    if (optionsOrSignal instanceof AbortSignal) {
      signal = optionsOrSignal;
    } else if (optionsOrSignal && typeof optionsOrSignal === 'object') {
      signal = optionsOrSignal.signal;
      if (optionsOrSignal.selectedFaceA !== null && optionsOrSignal.selectedFaceA !== undefined) {
        formData.append('selected_face_a', String(optionsOrSignal.selectedFaceA));
      }
      if (optionsOrSignal.selectedFaceB !== null && optionsOrSignal.selectedFaceB !== undefined) {
        formData.append('selected_face_b', String(optionsOrSignal.selectedFaceB));
      }
      if (optionsOrSignal.cropBoxA) {
        formData.append('crop_box_a', JSON.stringify(optionsOrSignal.cropBoxA));
      }
      if (optionsOrSignal.cropBoxB) {
        formData.append('crop_box_b', JSON.stringify(optionsOrSignal.cropBoxB));
      }
      if (optionsOrSignal.thresholdProfile) {
        formData.append('threshold_profile', optionsOrSignal.thresholdProfile);
      }
      if (optionsOrSignal.customThreshold !== undefined && optionsOrSignal.customThreshold !== null) {
        formData.append('custom_threshold', String(optionsOrSignal.customThreshold));
      }
    }

    const res = await fetch(`${API_BASE_URL}/api/compare`, {
      method: 'POST',
      body: formData,
      signal,
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({ detail: res.statusText }));
      throw new ApiError(
        errBody.detail || `Comparison request rejected with status ${res.status}`,
        res.status
      );
    }

    return await res.json();
  } catch (err: unknown) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw err;
    }
    if (err instanceof ApiError) throw err;
    throw new ApiError('Failed to execute comparison request.');
  }
}

// ==========================================
// STEP 05: Benchmark API Client Functions
// ==========================================

export async function fetchBenchmarkDatasets(): Promise<DatasetMetadata[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/benchmarks/datasets`);
    if (!res.ok) {
      throw new ApiError(`Failed to fetch datasets: ${res.statusText}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Network error connecting to benchmark datasets endpoint.');
  }
}

export async function fetchBenchmarkHistory(): Promise<BenchmarkRunSummary[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/benchmarks/history`);
    if (!res.ok) {
      throw new ApiError(`Failed to fetch benchmark history: ${res.statusText}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Network error connecting to benchmark history endpoint.');
  }
}

export async function fetchBenchmarkRun(runId: string): Promise<BenchmarkResult> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/benchmarks/runs/${encodeURIComponent(runId)}`);
    if (!res.ok) {
      throw new ApiError(`Failed to fetch benchmark run: ${res.statusText}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Network error retrieving benchmark telemetry.');
  }
}

export async function executeBenchmarkRun(config: BenchmarkRunConfig): Promise<BenchmarkResult> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/benchmarks/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({ detail: res.statusText }));
      throw new ApiError(
        errBody.detail || `Benchmark run rejected with status ${res.status}`,
        res.status
      );
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Failed to execute benchmark run.');
  }
}

export async function fetchDatasetStatus(datasetId: string): Promise<{
  dataset_id: string;
  status: string;
  progress_percent: number;
  message: string;
  details?: Record<string, unknown>;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/benchmarks/datasets/${encodeURIComponent(datasetId)}/status`);
    if (!res.ok) {
      throw new ApiError(`Failed to fetch dataset status: ${res.statusText}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Network error checking dataset installation status.');
  }
}

export async function installDataset(datasetId: string): Promise<{
  status: string;
  details?: Record<string, unknown>;
  error?: string;
}> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/benchmarks/datasets/${encodeURIComponent(datasetId)}/install`, {
      method: 'POST',
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({ detail: res.statusText }));
      throw new ApiError(errBody.detail || `Dataset install failed: ${res.statusText}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Network error triggering dataset installation.');
  }
}

export function getBenchmarkExportUrl(runId: string, format: 'json' | 'csv' | 'markdown'): string {
  return `${API_BASE_URL}/api/benchmarks/runs/${encodeURIComponent(runId)}/export/${format}`;
}

/**
 * Check backend readiness (models loaded and database connected).
 */
export async function fetchReadiness(): Promise<ReadinessResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/ready`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new ApiError(`Readiness check failed with status ${res.status}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Readiness probe unavailable.');
  }
}

/**
 * Fetch aggregated production dashboard statistics from SQLite.
 */
export async function fetchDashboardStats(): Promise<DashboardStatsResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/dashboard/stats`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new ApiError(`Failed to fetch dashboard stats: ${res.statusText}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Network error connecting to dashboard stats endpoint.');
  }
}

/**
 * Fetch recent comparison audit log records from SQLite.
 */
export async function fetchComparisonHistory(limit = 20): Promise<ComparisonHistoryRecord[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/history?limit=${encodeURIComponent(limit)}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new ApiError(`Failed to fetch comparison history: ${res.statusText}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Network error connecting to history endpoint.');
  }
}

/**
 * Clear comparison audit history from SQLite.
 */
export async function clearComparisonHistory(): Promise<{ deleted: number }> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/history`, {
      method: 'DELETE',
      headers: { Accept: 'application/json' },
    });
    if (!res.ok) {
      throw new ApiError(`Failed to clear history: ${res.statusText}`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Network error clearing comparison history.');
  }
}

export { API_BASE_URL };

