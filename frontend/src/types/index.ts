/**
 * Core type definitions for FACECORE AI.
 */

export type NavTab = 'compare' | 'testlab' | 'benchmarks' | 'settings';

export type Theme = 'cyber-dark' | 'tactical-charcoal' | 'slate-minimal';

export type EngineStatus = 'pending_integration' | 'active' | 'degraded' | 'offline';

export interface ImageQualityDiagnostics {
  filename: string;
  format: string;
  color_mode: string;
  width: int_number;
  height: int_number;
  aspect_ratio: string;
  file_size_bytes: number;
  sha256_hash: string;
  estimated_sharpness: number;
  contrast_std: number;
  brightness_mean: number;
  resolution_category: string;
  passes_quality_check: boolean;
  warnings: string[];
}

type int_number = number;

export interface ImageValidationResponse {
  is_valid: boolean;
  error_message: string | null;
  diagnostics: ImageQualityDiagnostics | null;
}

export interface EngineMetadata {
  engine_id: string;
  name: string;
  version: string;
  status: EngineStatus;
  is_mock_data: boolean;
  description: string;
  supported_models: string[];
}

export interface ComparisonResponse {
  status: string;
  timestamp: string;
  engine: EngineMetadata;
  image_a_diagnostics: ImageQualityDiagnostics;
  image_b_diagnostics: ImageQualityDiagnostics;
  similarity_score: number | null;
  is_match: boolean | null;
  interpretation_notice: string;
}

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  timestamp: string;
  engine_status: EngineStatus;
  security_mode: string;
}

export interface UploadedImageSlot {
  id: 'probe' | 'reference';
  label: string;
  file: File | null;
  previewUrl: string | null;
  diagnostics: ImageQualityDiagnostics | null;
  isValidating: boolean;
  validationError: string | null;
}

export interface ComparisonHistoryEntry {
  id: string;
  timestamp: string;
  imageAName: string;
  imageBName: string;
  hashAPrefix: string;
  hashBPrefix: string;
  dimensionsA: string;
  dimensionsB: string;
  engineName: string;
  statusNotice: string;
}
