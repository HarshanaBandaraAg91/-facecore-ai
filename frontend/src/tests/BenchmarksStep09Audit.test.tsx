import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BenchmarksView } from '../components/benchmarks/BenchmarksView';
import { ScientificAuditView } from '../components/benchmarks/ScientificAuditView';
import * as api from '../../src/services/api';
import type { DatasetMetadata, BenchmarkResult } from '../../src/types';

vi.mock('../../src/services/api', () => ({
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
    dataset_type: 'real',
    installation_status: 'VERIFIED',
  },
];

const mockLfwRun: BenchmarkResult = {
  run_id: 'step09-lfw-audit-run',
  dataset_id: 'lfw-canonical-v1',
  dataset_name: 'Labeled Faces in the Wild (LFW)',
  model_name: 'SFace (SphereFace2)',
  model_version: '2021dec-2023mar',
  timestamp: '2026-11-02T13:45:00Z',
  status: 'COMPLETED',
  total_pairs: 6000,
  genuine_pairs: 3000,
  impostor_pairs: 3000,
  eer: 0.0080,
  eer_threshold: 0.3132,
  auc: 0.9988,
  optimal_threshold: 0.3132,
  accuracy: 0.9935,
  confidence_intervals: [],
  confusion_matrix: {
    tp: 2980,
    fp: 19,
    tn: 2981,
    fn: 20,
    accuracy: 0.9935,
    precision: 0.9937,
    recall: 0.9933,
    f1_score: 0.9935,
  },
  tar_at_far_table: [],
  roc_curve: [],
  far_frr_curve: [],
  robustness_results: [],
  execution_time_seconds: 349.1,
  yunet_weights_hash: '8fb616bb1c2c366ff641320478db1aa22769399df2c295beee3c3143c68a4170',
  sface_weights_hash: 'c5f59040ab50f38b4c023d8c1be276f571b782c5e533c3756c39f201e74f8ee6',
  pair_list_hash: '6c66cf17812ea2c153cb1c1d85608b6b0632a4e7',
  reproducibility_command: 'python -m app.benchmarks.cli --dataset lfw-canonical-v1 --seed 42',
  official_total_pairs: 6000,
  resolved_pairs_count: 6000,
  unresolved_pairs_count: 0,
  missing_images_count: 0,
  evaluation_completeness: 'COMPLETE_OFFICIAL_CORPUS',
};

describe('BenchmarksStep09Audit (Scientific Validation & Reproduction)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchBenchmarkDatasets).mockResolvedValue(mockDatasets);
    vi.mocked(api.fetchBenchmarkHistory).mockResolvedValue([
      {
        run_id: 'step09-lfw-audit-run',
        dataset_id: 'lfw-canonical-v1',
        dataset_name: 'Labeled Faces in the Wild (LFW)',
        timestamp: '2026-11-02T13:45:00Z',
        status: 'COMPLETED',
        total_pairs: 6000,
        eer: 0.0080,
        auc: 0.9988,
        accuracy: 0.9935,
        execution_time_seconds: 349.1,
      },
    ]);
    vi.mocked(api.fetchBenchmarkRun).mockResolvedValue(mockLfwRun);
  });

  it('renders mode switcher buttons between Active Benchmarks and Step 09 Audit', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByTestId('toggle-benchmarks-tab')).toBeInTheDocument();
      expect(screen.getByTestId('toggle-audit-tab')).toBeInTheDocument();
      expect(screen.getByText('Active Benchmark Console')).toBeInTheDocument();
      expect(screen.getByText('Step 09 Scientific Audit & Reproduction')).toBeInTheDocument();
    });
  });

  it('switches to ScientificAuditView when Step 09 Audit tab is clicked', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByTestId('toggle-audit-tab')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('toggle-audit-tab'));

    await waitFor(() => {
      expect(
        screen.getByText(/Full-Scale Dataset Evaluation & Completeness Accounting Matrix/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/Audit Discrepancy Register & Resolution Tracker/i)).toBeInTheDocument();
    });
  });

  it('renders all official dataset completeness entries in ScientificAuditView', () => {
    render(<ScientificAuditView />);

    expect(screen.getAllByText('LFW Canonical').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Cross-Age LFW (CALFW)').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Cross-Pose LFW (CPLFW)').length).toBeGreaterThan(0);
    expect(screen.getByText('CFP-FP')).toBeInTheDocument();
    expect(screen.getByText('AgeDB-30')).toBeInTheDocument();

    // Verifies accounting numbers
    expect(screen.getByText(/6,000 \/ 6,000 \(100\.0%\)/i)).toBeInTheDocument();
    expect(screen.getByText(/2,424 \/ 6,000 \(40\.40%\)/i)).toBeInTheDocument();
    expect(screen.getByText(/2,494 \/ 6,000 \(41\.57%\)/i)).toBeInTheDocument();
  });

  it('renders the Discrepancy Register items DISC-01 through DISC-08', () => {
    render(<ScientificAuditView />);

    expect(screen.getByText('DISC-01')).toBeInTheDocument();
    expect(screen.getByText('DISC-02')).toBeInTheDocument();
    expect(screen.getByText('DISC-03')).toBeInTheDocument();
    expect(screen.getByText('DISC-08')).toBeInTheDocument();
    expect(screen.getByText(/Silent pair omission in CALFW and CPLFW CSV parsers/i)).toBeInTheDocument();
    expect(screen.getByText(/Unexplained threshold divergence between CALFW/i)).toBeInTheDocument();
  });

  it('renders reproduction CLI commands and handles copy interaction', () => {
    // Mock navigator.clipboard
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    });

    render(<ScientificAuditView />);

    const copyButtons = screen.getAllByText(/Copy Command/i);
    expect(copyButtons.length).toBeGreaterThan(0);

    fireEvent.click(copyButtons[0]);
    expect(writeTextMock).toHaveBeenCalledWith(
      expect.stringContaining('python -m app.benchmarks.runner')
    );
  });
});
