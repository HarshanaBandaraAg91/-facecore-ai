/**
 * API client service for communicating with FACECORE AI backend.
 */

import type {
  HealthResponse,
  EngineMetadata,
  ImageValidationResponse,
  ComparisonResponse,
} from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

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
 * Validate an image file through backend security and quality diagnostics.
 */
export async function validateImageApi(file: File): Promise<ImageValidationResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);

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
 * Submit two validated images for facial comparison evaluation.
 */
export async function compareImagesApi(
  fileA: File,
  fileB: File
): Promise<ComparisonResponse> {
  try {
    const formData = new FormData();
    formData.append('image_a', fileA);
    formData.append('image_b', fileB);

    const res = await fetch(`${API_BASE_URL}/api/compare`, {
      method: 'POST',
      body: formData,
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
    if (err instanceof ApiError) throw err;
    throw new ApiError('Failed to execute comparison request.');
  }
}

export { API_BASE_URL };
