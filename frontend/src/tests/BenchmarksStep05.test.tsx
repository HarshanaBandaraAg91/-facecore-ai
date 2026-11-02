import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BenchmarksView } from '../components/benchmarks/BenchmarksView';
import * as api from '../services/api';
import type { DatasetMetadata, BenchmarkResult, BenchmarkRunSummary } from '../types';

const mockDatasets: DatasetMetadata[] = [
  {
    dataset_id: 'lfw-canonical-v1',
    name: 'Labeled Faces in the Wild (LFW)',
    description: 'Standard 10-fold unconstrained facial verification protocol across 6,000 official pairs.',
    total_images: 13233,
    total_identities: 5749,
    total_pairs: 6000,
    verification_status: 'UNRUN',
    is_available: true,
    license: 'Non-Commercial Academic Research (UMass Amherst)',
    source_url: 'http://vis-www.cs.umass.edu/lfw/',
  },
  {
    dataset_id: 'facecore-synthetic-fixture-v1',
    name: 'FACECORE Synthetic Benchmark Fixture',
    description: 'Deterministic local 10-fold verification benchmark (60 genuine, 60 impostor pairs) for instant offline CI.',
    total_images: 120,
    total_identities: 20,
    total_pairs: 120,
    verification_status: 'DATASET_VERIFIED',
    is_available: true,
    license: 'Apache-2.0 (Internal Test Fixture)',
    source_url: 'local://fixtures/synthetic-v1',
  },
];

const mockResult: BenchmarkResult = {
  run_id: 'run_20261102_120000_abc123',
  dataset_id: 'facecore-synthetic-fixture-v1',
  dataset_name: 'FACECORE Synthetic Benchmark Fixture',
  model_name: 'SFace (SphereFace2)',
  model_version: '2021dec-2023mar',
  timestamp: '2026-11-02T12:00:00Z',
  status: 'COMPLETED',
  total_pairs: 60,
  genuine_pairs: 30,
  impostor_pairs: 30,
  eer: 0.125,
  eer_threshold: 0.362,
  auc: 0.9421,
  optimal_threshold: 0.385,
  accuracy: 0.875,
  confidence_intervals: [
    {
      metric: 'Accuracy',
      mean: 0.875,
      ci_lower: 0.821,
      ci_upper: 0.915,
      confidence_level: 0.95,
    },
    {
      metric: 'EER',
      mean: 0.125,
      ci_lower: 0.102,
      ci_upper: 0.154,
      confidence_level: 0.95,
    },
  ],
  confusion_matrix: {
    tp: 26,
    fp: 4,
    tn: 26,
    fn: 4,
    accuracy: 0.8667,
    precision: 0.8667,
    recall: 0.8667,
    f1_score: 0.8667,
  },
  tar_at_far_table: [
    { far_target: 0.01, tar: 0.782, threshold: 0.45 },
    { far_target: 0.05, tar: 0.850, threshold: 0.40 },
    { far_target: 0.10, tar: 0.920, threshold: 0.35 },
  ],
  roc_curve: [
    { threshold: 0.8, far: 0.0, frr: 0.5, tar: 0.5, precision: 1.0, recall: 0.5 },
    { threshold: 0.362, far: 0.125, frr: 0.125, tar: 0.875, precision: 0.875, recall: 0.875 },
    { threshold: 0.1, far: 0.8, frr: 0.0, tar: 1.0, precision: 0.55, recall: 1.0 },
  ],
  far_frr_curve: [],
  robustness_results: [
    {
      condition_name: 'Gaussian Blur (Light)',
      description: '5x5 Gaussian blur with sigma=1.5',
      sample_size: 30,
      accuracy: 0.833,
      eer: 0.142,
      auc: 0.910,
      tar_at_far_01: 0.720,
    },
  ],
  execution_time_seconds: 1.42,
};

const mockHistory: BenchmarkRunSummary[] = [
  {
    run_id: 'run_20261102_120000_abc123',
    dataset_id: 'facecore-synthetic-fixture-v1',
    dataset_name: 'FACECORE Synthetic Benchmark Fixture',
    timestamp: '2026-11-02T12:00:00Z',
    status: 'COMPLETED',
    total_pairs: 60,
    eer: 0.125,
    auc: 0.9421,
    accuracy: 0.875,
    execution_time_seconds: 1.42,
  },
];

vi.mock('../services/api', () => ({
  fetchBenchmarkDatasets: vi.fn(),
  fetchBenchmarkHistory: vi.fn(),
  fetchBenchmarkRun: vi.fn(),
  executeBenchmarkRun: vi.fn(),
  getBenchmarkExportUrl: vi.fn((runId: string, format: string) => `/api/benchmarks/runs/${runId}/export/${format}`),
}));

describe('STEP 05: BenchmarksView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchBenchmarkDatasets).mockResolvedValue(mockDatasets);
    vi.mocked(api.fetchBenchmarkHistory).mockResolvedValue(mockHistory);
    vi.mocked(api.fetchBenchmarkRun).mockResolvedValue(mockResult);
    vi.mocked(api.executeBenchmarkRun).mockResolvedValue(mockResult);
  });

  it('renders benchmark header, scientific integrity directive, and dataset registry', async () => {
    render(<BenchmarksView />);

    expect(screen.getByText(/Standardized Model Benchmarks & Scientific Verification Suite/i)).toBeDefined();
    expect(screen.getByText(/SCIENTIFIC INTEGRITY DIRECTIVE/i)).toBeDefined();
    expect(screen.getByText(/Cosine similarity scores represent distance metrics/i)).toBeDefined();

    await waitFor(() => {
      expect(screen.getAllByText(/Labeled Faces in the Wild/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/FACECORE Synthetic Benchmark Fixture/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('displays primary evaluation metric cards when run results are loaded', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getAllByText(/0\.9421/).length).toBeGreaterThanOrEqual(1); // AUC
      expect(screen.getAllByText(/12\.50%/).length).toBeGreaterThanOrEqual(1); // EER
      expect(screen.getAllByText(/87\.50%/).length).toBeGreaterThanOrEqual(1); // Accuracy
      expect(screen.getAllByText(/0\.3850/).length).toBeGreaterThanOrEqual(1); // Optimal Threshold
      expect(screen.getAllByText(/78\.2%/).length).toBeGreaterThanOrEqual(1); // TAR @ FAR=1%
      expect(screen.getByText(/EVALUATION SAMPLE SIZE/i)).toBeDefined();
    });
  });

  it('renders confusion matrix and operational operating points table', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByText(/Confusion Matrix & Error Breakdown/i)).toBeDefined();
      expect(screen.getByText(/TRUE POSITIVES \(TP\)/i)).toBeDefined();
      expect(screen.getByText(/Operational Operating Points \(TAR @ FAR\)/i)).toBeDefined();
      expect(screen.getByText(/Gaussian Blur \(Light\)/i)).toBeDefined();
    });
  });

  it('renders export buttons for JSON report and pairwise CSV', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByText(/Export JSON Report/i)).toBeDefined();
      expect(screen.getByText(/Export Pairwise CSV/i)).toBeDefined();
    });
  });

  it('triggers executeBenchmarkRun when Execute Model Benchmark button is clicked', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Execute Model Benchmark/i })).toBeDefined();
    });

    const runButton = screen.getByRole('button', { name: /Execute Model Benchmark/i });
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(api.executeBenchmarkRun).toHaveBeenCalledWith(
        expect.objectContaining({
          dataset_id: 'facecore-synthetic-fixture-v1',
          evaluate_robustness: true,
        })
      );
    });
  });
});
