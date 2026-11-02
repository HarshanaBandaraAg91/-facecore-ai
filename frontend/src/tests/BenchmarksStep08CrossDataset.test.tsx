import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BenchmarksView } from '../components/benchmarks/BenchmarksView';
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
  {
    dataset_id: 'calfw-v1',
    name: 'Cross-Age LFW (CALFW)',
    description: 'Cross-age face verification benchmark across 6,000 pairs with maximized chronological age gaps.',
    total_images: 12174,
    total_identities: 4025,
    total_pairs: 6000,
    verification_status: 'DATASET_VERIFIED',
    is_available: true,
    license: 'Non-Commercial Academic Research (Tsinghua / BUPT)',
    source_url: 'http://whdeng.cn/CALFW/index.html',
    dataset_type: 'real',
    installation_status: 'VERIFIED',
  },
  {
    dataset_id: 'cplfw-v1',
    name: 'Cross-Pose LFW (CPLFW)',
    description: 'Cross-pose face verification benchmark across 6,000 pairs with maximized yaw variation.',
    total_images: 11652,
    total_identities: 3998,
    total_pairs: 6000,
    verification_status: 'DATASET_VERIFIED',
    is_available: true,
    license: 'Non-Commercial Academic Research (Tsinghua / BUPT)',
    source_url: 'http://whdeng.cn/CPLFW/index.html',
    dataset_type: 'real',
    installation_status: 'VERIFIED',
  },
  {
    dataset_id: 'cfp-fp-v1',
    name: 'Celebrities in Frontal-Profile (CFP-FP)',
    description: 'Extreme cross-pose verification benchmark across 7,000 pairs.',
    total_images: 7000,
    total_identities: 500,
    total_pairs: 7000,
    verification_status: 'UNRUN',
    is_available: false,
    license: 'Academic Research Agreement (UMD)',
    source_url: 'http://www.cfpdb.org/',
    dataset_type: 'real',
    installation_status: 'NOT_INSTALLED',
  },
  {
    dataset_id: 'agedb-30-v1',
    name: 'AgeDB-30 (Temporal 30-Year Gap)',
    description: 'Cross-age verification benchmark with 30-year chronological aging gap.',
    total_images: 16488,
    total_identities: 568,
    total_pairs: 6000,
    verification_status: 'UNRUN',
    is_available: false,
    license: 'CC BY-NC 4.0 (Imperial College London iBUG)',
    source_url: 'https://ibug.doc.ic.ac.uk/resources/agedb/',
    dataset_type: 'real',
    installation_status: 'RESTRICTED_ACCESS',
  },
];

const mockCplfwRun: BenchmarkResult = {
  run_id: 'run_cplfw_step08_001',
  dataset_id: 'cplfw-v1',
  dataset_name: 'Cross-Pose LFW (CPLFW)',
  model_name: 'SFace (SphereFace2)',
  model_version: '2021dec-2023mar',
  timestamp: '2026-11-02T12:00:00Z',
  status: 'COMPLETED',
  total_pairs: 60,
  genuine_pairs: 30,
  impostor_pairs: 30,
  eer: 0.0333,
  eer_threshold: 0.3407,
  auc: 0.9989,
  optimal_threshold: 0.3407,
  accuracy: 0.9667,
  confidence_intervals: [],
  confusion_matrix: {
    tp: 29,
    fp: 1,
    tn: 29,
    fn: 1,
    accuracy: 0.9667,
    precision: 0.9667,
    recall: 0.9667,
    f1_score: 0.9667,
  },
  tar_at_far_table: [],
  roc_curve: [],
  far_frr_curve: [],
  robustness_results: [],
  execution_time_seconds: 4.5,
  is_real_photographs: true,
  transferred_threshold: 0.3128,
  transferred_threshold_source: 'LFW Validation Calibrated (tau=0.3128)',
  transferred_accuracy: 0.9500,
  transferred_confusion_matrix: {
    tp: 30,
    fp: 3,
    tn: 27,
    fn: 0,
    accuracy: 0.9500,
    precision: 0.9091,
    recall: 1.0000,
    f1_score: 0.9524,
  },
  cross_dataset_condition: 'cross_pose',
};

describe('STEP 08: Cross-Dataset Generalization & Robustness UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchBenchmarkDatasets).mockResolvedValue(mockDatasets);
    vi.mocked(api.fetchBenchmarkHistory).mockResolvedValue([
      {
        run_id: 'run_cplfw_step08_001',
        dataset_id: 'cplfw-v1',
        dataset_name: 'Cross-Pose LFW (CPLFW)',
        timestamp: '2026-11-02T12:00:00Z',
        status: 'COMPLETED',
        total_pairs: 60,
        eer: 0.0333,
        auc: 0.9989,
        accuracy: 0.9667,
        execution_time_seconds: 4.5,
      },
    ]);
    vi.mocked(api.fetchBenchmarkRun).mockResolvedValue(mockCplfwRun);
  });

  it('renders cross-dataset options in the dataset catalog and controller selector', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getAllByText('Cross-Age LFW (CALFW)').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Cross-Pose LFW (CPLFW)').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Celebrities in Frontal-Profile (CFP-FP)').length).toBeGreaterThan(0);
      expect(screen.getAllByText('AgeDB-30 (Temporal 30-Year Gap)').length).toBeGreaterThan(0);
    });
  });

  it('displays the threshold generalization panel with native vs transferred metrics', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByText('Cross-Dataset Threshold Generalization Audit')).toBeInTheDocument();
      expect(screen.getByText('DATASET NATIVE THRESHOLD')).toBeInTheDocument();
      expect(screen.getByText('TRANSFERRED LFW THRESHOLD')).toBeInTheDocument();
      expect(screen.getByText('TRANSFER GAP (Δ ACCURACY)')).toBeInTheDocument();
    });
  });

  it('renders Markdown report export button alongside JSON and CSV', async () => {
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByText('Export Markdown')).toBeInTheDocument();
      expect(screen.getByText('Export JSON Report')).toBeInTheDocument();
      expect(screen.getByText('Export Pairwise CSV')).toBeInTheDocument();
    });
  });

  it('passes configured transfer threshold to executeBenchmarkRun', async () => {
    vi.mocked(api.executeBenchmarkRun).mockResolvedValue(mockCplfwRun);
    render(<BenchmarksView />);

    await waitFor(() => {
      expect(screen.getByText('Execute Model Benchmark')).toBeInTheDocument();
    });

    const runBtn = screen.getByText('Execute Model Benchmark');
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(api.executeBenchmarkRun).toHaveBeenCalledWith(
        expect.objectContaining({
          transfer_threshold: 0.3128,
        })
      );
    });
  });
});
