/**
 * Core type definitions for FACECORE AI (Step 02 - Real Embedding Engine).
 */

export type NavTab = 'dashboard' | 'compare' | 'testlab' | 'benchmarks' | 'settings';

export type Theme = 'cyber-dark' | 'tactical-charcoal' | 'slate-minimal';

export type EngineStatus = 'pending_integration' | 'active' | 'degraded' | 'offline';

export type ThresholdProfile = 'high_security' | 'balanced' | 'high_convenience' | 'custom';

export interface DetectedFaceSummary {
  index: number;
  box: [number, number, number, number];
  confidence: number;
  landmarks?: number[][];
  quality_advisories?: string[];
}

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
  detected_faces?: DetectedFaceSummary[];
  selected_face_index?: number | null;
  crop_bounding_box?: number[] | null;
  
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
  detection_latency_ms?: number | null;
  embedding_latency_ms?: number | null;
  threshold_profile?: string | null;
  threshold_used?: number | null;
  decision?: 'MATCH' | 'NO_MATCH' | 'INDETERMINATE' | string | null;
  statistical_confidence_notice?: string | null;
  interpretation_notice: string;
  ethical_disclaimer?: string;
}

export interface ComparisonHistoryRecord {
  id: string;
  timestamp: string;
  probe_hash_prefix: string;
  reference_hash_prefix: string;
  similarity_score: number | null;
  threshold_profile: string;
  threshold_used: number;
  decision: string;
  inference_latency_ms: number | null;
  has_quality_warnings: boolean;
  status: string;
}

export interface DashboardStatsResponse {
  total_comparisons: number;
  successful_matches: number;
  successful_non_matches: number;
  failed_comparisons: number;
  average_latency_ms: number;
  total_fta_events: number;
  fta_rate_percent: number;
  fta_breakdown: Record<string, number>;
  database_size_bytes: number;
  schema_version: number;
}

export interface ReadinessResponse {
  ready: boolean;
  status: string;
  models_loaded: boolean;
  database_connected: boolean;
  active_threshold_profile: string;
  timestamp: string;
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
  selectedFaceIndex?: number | null;
  cropBox?: [number, number, number, number] | null;
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

export type ComparisonProcessingState =
  | 'idle'
  | 'validating'
  | 'processing'
  | 'completing'
  | 'success'
  | 'error';

export interface ComparisonStageInfo {
  id: string;
  label: string;
  detail: string;
}

// ==========================================
// STEP 05: Benchmark Framework Type Definitions
// ==========================================

export type DatasetStatus =
  | 'UNRUN'
  | 'DATASET_VERIFIED'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED';

export interface DatasetMetadata {
  dataset_id: string;
  name: string;
  description: string;
  total_images: number;
  total_identities: number;
  total_pairs: number;
  verification_status: DatasetStatus;
  is_available: boolean;
  license: string;
  source_url: string;
  local_path?: string | null;
  dataset_type?: string;
  installation_status?: string;
}

export interface FTABreakdown {
  no_face_detected: number;
  multiple_faces_detected: number;
  alignment_failed: number;
  inference_error: number;
}

export interface ROCCurvePoint {
  threshold: number;
  far: number;
  frr: number;
  tar: number;
  precision: number;
  recall: number;
}

export interface TARAtFAR {
  far_target: number;
  tar: number;
  threshold: number;
}

export interface ConfusionMatrix {
  tp: number;
  fp: number;
  tn: number;
  fn: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
}

export interface ConfidenceInterval {
  metric: string;
  mean: number;
  ci_lower: number;
  ci_upper: number;
  confidence_level: number;
}

export interface RobustnessConditionResult {
  condition_name: string;
  description: string;
  sample_size: number;
  accuracy: number;
  eer: number;
  auc: number;
  tar_at_far_01: number;
  attempted_pairs?: number | null;
  successful_pairs?: number | null;
  failed_pairs?: number | null;
  fta_rate?: number | null;
  genuine_mean?: number | null;
  impostor_mean?: number | null;
  far_at_baseline_thresh?: number | null;
  frr_at_baseline_thresh?: number | null;
}

export interface BenchmarkResult {
  run_id: string;
  dataset_id: string;
  dataset_name: string;
  model_name: string;
  model_version: string;
  timestamp: string;
  status: DatasetStatus;
  total_pairs: number;
  genuine_pairs: number;
  impostor_pairs: number;
  eer: number;
  eer_threshold: number;
  auc: number;
  optimal_threshold: number;
  accuracy: number;
  confidence_intervals: ConfidenceInterval[];
  confusion_matrix: ConfusionMatrix;
  tar_at_far_table: TARAtFAR[];
  roc_curve: ROCCurvePoint[];
  far_frr_curve: ROCCurvePoint[];
  robustness_results: RobustnessConditionResult[];
  execution_time_seconds: number;
  error_message?: string | null;
  dataset_manifest_hash?: string | null;
  model_weights_hash?: string | null;
  evaluation_protocol?: string | null;
  total_requested_pairs?: number | null;
  failure_to_acquire_count?: number | null;
  failure_to_acquire_rate?: number | null;
  fta_breakdown?: FTABreakdown | null;
  is_real_photographs?: boolean;
  bootstrap_method?: string | null;
  transferred_threshold?: number | null;
  transferred_threshold_source?: string | null;
  transferred_accuracy?: number | null;
  transferred_confusion_matrix?: ConfusionMatrix | null;
  cross_dataset_condition?: string | null;
  yunet_weights_hash?: string | null;
  sface_weights_hash?: string | null;
  pair_list_hash?: string | null;
  reproducibility_command?: string | null;
  official_total_pairs?: number | null;
  resolved_pairs_count?: number | null;
  unresolved_pairs_count?: number | null;
  missing_images_count?: number | null;
  evaluation_completeness?: string | null;
  metric_calculation_version?: string | null;
}

export interface BenchmarkRunSummary {
  run_id: string;
  dataset_id: string;
  dataset_name: string;
  timestamp: string;
  status: DatasetStatus;
  total_pairs: number;
  eer: number;
  auc: number;
  accuracy: number;
  execution_time_seconds: number;
}

export interface BenchmarkRunConfig {
  dataset_id: string;
  evaluate_robustness?: boolean;
  max_pairs?: number | null;
  random_seed?: number;
  face_selection_policy?: 'center_face' | 'strict_single_face';
  transfer_threshold?: number | null;
  description?: string | null;
}
