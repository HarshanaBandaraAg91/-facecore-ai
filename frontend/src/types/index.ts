/**
 * Core type definitions for FACECORE AI (Step 02 - Real Embedding Engine).
 */

export type NavTab = 'compare' | 'testlab' | 'benchmarks' | 'settings';

export type Theme = 'cyber-dark' | 'tactical-charcoal' | 'slate-minimal';

export type EngineStatus = 'pending_integration' | 'active' | 'degraded' | 'offline';

export interface ImageQualityDiagnostics {
  filename: string;
  format: string;
  color_mode: string;
  width: number;
  height: number;
  aspect_ratio: string;
  file_size_bytes: number;
  sha256_hash: string;
  estimated_sharpness: number;
  contrast_std: number;
  brightness_mean: number;
  resolution_category: string;
  
  // Face detection telemetry
  face_detected?: boolean;
  face_count?: number;
  face_confidence?: number | null;
  face_bounding_box?: number[] | null;
  
  passes_quality_check: boolean;
  warnings: string[];
}

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
  embedding_dimension?: number;
  inference_device?: string;
  weights_license?: string;
  preprocessing_details?: string;
}

export interface ComparisonResponse {
  status: string;
  timestamp: string;
  engine: EngineMetadata;
  image_a_diagnostics: ImageQualityDiagnostics;
  image_b_diagnostics: ImageQualityDiagnostics;
  similarity_score: number | null;
  raw_cosine_similarity: number | null;
  transformed_display_score: number | null;
  provisional_threshold: number | null;
  is_match: boolean | null;
  threshold_notice: string | null;
  inference_latency_ms: number | null;
  interpretation_notice: string;
  ethical_disclaimer?: string;
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
  rawCosineScore?: number | null;
  displayScore?: number | null;
  isMatch?: boolean | null;
}
