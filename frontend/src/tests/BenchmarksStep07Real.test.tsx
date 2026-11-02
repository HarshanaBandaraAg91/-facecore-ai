import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BenchmarksView } from '../components/benchmarks/BenchmarksView';
import * as api from '../services/api';
import type { DatasetMetadata, BenchmarkRunSummary, BenchmarkResult } from '../types';

vi.mock('../services/api', () => ({
  fetchBenchmarkDatasets: vi.fn(),
  fetchBenchmarkHistory: vi.fn(),
  fetchBenchmarkRun: vi.fn(),
  executeBenchmarkRun: vi.fn(),
  installDataset: vi.fn(),
  fetchDatasetStatus: vi.fn(),
  getBenchmarkExportUrl: vi.fn((id, fmt) => `/api/benchmarks/runs/${id}/export/${fmt}`),
}));

const mockDatasets: DatasetMetadata[] = [
  {
    dataset_id: 'lfw-canonical-v1',
    name: 'Labeled Faces in the Wild (LFW)',
    description: 'Standard 10-fold unconstrained facial verification protocol across 6,000 official pairs.',
    total_images: 13233,
    total_identities: 5749,
    total_pairs: 6000,
    verification_status: 'DATASET_VERIFIED',
    is_available: true,
    license: 'Non-Commercial Academic Research (UMass Amherst)',
    source_url: 'http://vis-www.cs.umass.edu/lfw/',
    local_path: 'backend/data/lfw/images',
    dataset_type: 'real',
    installation_status: 'VERIFIED',
  },
  {
    dataset_id: 'facecore-synthetic-fixture-v1',
    name: 'FACECORE Synthetic Benchmark Fixture',
    description: 'Deterministic local 10-fold verification benchmark (60 genuine, 60 impostor pairs).',
    total_images: 120,
    total_identities: 20,
    total_pairs: 120,
    verification_status: 'DATASET_VERIFIED',
    is_available: true,
    license: 'Apache-2.0 (Internal Test Fixture)',
    source_url: 'local://fixtures/synthetic-v1',
    dataset_type: 'synthetic',
    installation_status: 'VERIFIED',
  },
];

const mockRealLfwRun: BenchmarkResult = {
  run_id: 'run_20261102_real_lfw_01',
  dataset_id: 'lfw-canonical-v1',
  dataset_name: 'Labeled Faces in the Wild (LFW)',
  model_name: 'SFace (SphereFace2)',
  model_version: '2021dec-2023mar',
  timestamp: '2026-11-02T12:00:00Z',
  status: 'COMPLETED',
  total_pairs: 200,
  genuine_pairs: 100,
  impostor_pairs: 100,
  eer: 0.01,
  eer_threshold: 0.305,
  auc: 0.998,
  optimal_threshold: 0.315,
  accuracy: 0.985,
  confidence_intervals: [
    { metric: 'Accuracy', mean: 0.985, ci_lower: 0.965, ci_upper: 0.995, confidence_level: 0.95 },
    { metric: 'EER', mean: 0.01, ci_lower: 0.005, ci_upper: 0.025, confidence_level: 0.95 },
  ],
  confusion_matrix: {
    tp: 99,
    fp: 2,
    tn: 98,
    fn: 1,
    accuracy: 0.985,
    precision: 0.9802,
    recall: 0.99,
    f1_score: 0.9851,
  },
  tar_at_far_table: [
    { far_target: 0.01, tar: 0.98, threshold: 0.315 },
    { far_target: 0.001, tar: 0.92, threshold: 0.365 },
  ],
  roc_curve: [
    { threshold: 0.315, far: 0.02, frr: 0.01, tar: 0.99, precision: 0.98, recall: 0.99 },
  ],
  far_frr_curve: [],
  robustness_results: [],
  execution_time_seconds: 12.4,
  dataset_manifest_hash: 'abc123hash',
  model_weights_hash: 'sface:123|yunet:456',
  evaluation_protocol: '10-Fold Cross-Validation, Official LFW Protocol (View 2)',
  total_requested_pairs: 200,
  failure_to_acquire_count: 0,
  failure_to_acquire_rate: 0.0,
  is_real_photographs: true,
  fta_breakdown: {
    no_face_detected: 0,
    multiple_faces_detected: 0,
    alignment_failed: 0,
    inference_error: 0,
  },
};

const mockHistory: BenchmarkRunSummary[] = [
  {
    run_id: 'run_20261102_real_lfw_01',
    dataset_id: 'lfw-canonical-v1',
    dataset_name: 'Labeled Faces in the Wild (LFW)',
    timestamp: '2026-11-02T12:00:00Z',
    status: 'COMPLETED',
    total_pairs: 200,
    eer: 0.01,
    auc: 0.998,
    accuracy: 0.985,
    execution_time_seconds: 12.4,
  },
];

describe('STEP 07: Real-World Dataset Integration and Empirical SFace Benchmarking UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchBenchmarkDatasets).mockResolvedValue(mockDatasets);
    vi.mocked(api.fetchBenchmarkHistory).mockResolvedValue(mockHistory);
    vi.mocked(api.fetchBenchmarkRun).mockResolvedValue(mockRealLfwRun);
    vi.mocked(api.executeBenchmarkRun).mockResolvedValue(mockRealLfwRun);
  });

  it('renders dataset modalities distinguishing Real Photographs from Synthetic Fixtures', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getAllByText(/Real Photographs/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Synthetic Fixture/i).length).toBeGreaterThan(0);
    });
  });

  it('displays ISO/IEC 19795-1 Failure to Acquire (FTA) card and breakdown', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getAllByText(/FAILURE TO ACQUIRE/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/ISO\/IEC 19795-1 FTA BREAKDOWN:/i)).toBeDefined();
      expect(screen.getByText(/Zero Faces:/i)).toBeDefined();
      expect(screen.getByText(/Multiple Faces:/i)).toBeDefined();
    });
  });

  it('displays real research dataset provenance badge for LFW runs', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByText(/REAL RESEARCH DATASET/i)).toBeDefined();
      expect(screen.getByText(/Official LFW Protocol \(View 2\)/i)).toBeDefined();
    });
  });

  it('renders empirical comparison matrix contrasting Real Photographs and Synthetic Fixture', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByText(/Empirical Domain Comparison: Real Photographs \(LFW\) vs. Synthetic Fixture/i)).toBeDefined();
      expect(screen.getByText(/SFace weights were trained on real human faces/i)).toBeDefined();
    });
  });

  it('allows configuring face selection policy and executes benchmark with chosen policy', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByText(/Acquisition \/ Face Selection:/i)).toBeDefined();
    });

    const runBtn = screen.getByRole('button', { name: /Execute Model Benchmark/i });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(api.executeBenchmarkRun).toHaveBeenCalledWith(
        expect.objectContaining({
          face_selection_policy: 'center_face',
        })
      );
    });
  });
});
