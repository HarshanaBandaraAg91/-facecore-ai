import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ComparisonWorkspace } from '../components/comparison/ComparisonWorkspace';
import * as api from '../services/api';
import type { ComparisonResponse, ImageValidationResponse } from '../types';

vi.mock('../services/api', () => ({
  compareImagesApi: vi.fn(),
  validateImageApi: vi.fn(),
  fetchHealth: vi.fn(),
  fetchEngineInfo: vi.fn(),
}));

const mockDiagA = {
  filename: 'probe.jpg',
  format: 'JPEG',
  color_mode: 'RGB',
  width: 320,
  height: 320,
  aspect_ratio: '1:1',
  file_size_bytes: 35000,
  sha256_hash: 'abcdef1234567890',
  estimated_sharpness: 80.0,
  contrast_std: 35.0,
  brightness_mean: 128.0,
  resolution_category: 'Standard Definition',
  passes_quality_check: true,
  warnings: [],
};

const mockDiagB = {
  filename: 'reference.jpg',
  format: 'JPEG',
  color_mode: 'RGB',
  width: 320,
  height: 320,
  aspect_ratio: '1:1',
  file_size_bytes: 36000,
  sha256_hash: '0987654321fedcba',
  estimated_sharpness: 82.0,
  contrast_std: 36.0,
  brightness_mean: 130.0,
  resolution_category: 'Standard Definition',
  passes_quality_check: true,
  warnings: [],
};

const mockComparisonResponse: ComparisonResponse = {
  status: 'evaluation_completed',
  similarity_score: 0.7421,
  raw_cosine_similarity: 0.7421,
  transformed_display_score: 87.1,
  provisional_threshold: 0.363,
  is_match: true,
  threshold_notice: 'PROVISIONAL UNCALIBRATED BASELINE',
  inference_latency_ms: 22.4,
  timestamp: '2026-10-27T00:00:00Z',
  engine: {
    engine_id: 'facecore-sface-yunet-v2',
    name: 'SFace (SphereFace2) + YuNet',
    version: '2021dec-2023mar',
    status: 'active',
    is_mock_data: false,
    description: 'Local neural inference engine',
    supported_models: ['YuNet', 'SFace'],
    embedding_dimension: 128,
    inference_device: 'CPU',
    weights_license: 'Apache-2.0',
    preprocessing_details: 'YuNet 5-point landmark detection and affine crop',
  },
  image_a_diagnostics: {
    ...mockDiagA,
    face_detected: true,
    face_count: 1,
    face_confidence: 0.98,
    face_bounding_box: [40, 40, 200, 220],
  },
  image_b_diagnostics: {
    ...mockDiagB,
    face_detected: true,
    face_count: 1,
    face_confidence: 0.97,
    face_bounding_box: [42, 42, 198, 218],
  },
  interpretation_notice:
    'SFace cosine score of +0.7421 (transformed display index: 87.1/100). The provisional baseline threshold of 0.363 is uncalibrated.',
  ethical_disclaimer:
    'RESEARCH EVALUATION ONLY: Facial embedding similarity is an experimental metric and is NOT proof of identity.',
};

describe('Comparison Workflow & Staged Progress Machine (Step 03)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    globalThis.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    globalThis.URL.revokeObjectURL = vi.fn();

    // Default validation mock
    vi.mocked(api.validateImageApi).mockImplementation((file: File) => {
      const isA = file.name.includes('probe');
      return Promise.resolve<ImageValidationResponse>({
        is_valid: true,
        error_message: null,
        diagnostics: isA ? mockDiagA : mockDiagB,
      });
    });
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  const uploadTestFiles = async () => {
    const inputA = screen.getByTestId('file-input-probe');
    const inputB = screen.getByTestId('file-input-reference');
    const fileA = new File(['fake-jpg-bytes-probe'], 'probe.jpg', {
      type: 'image/jpeg',
    });
    const fileB = new File(['fake-jpg-bytes-ref'], 'reference.jpg', {
      type: 'image/jpeg',
    });

    fireEvent.change(inputA, { target: { files: [fileA] } });
    fireEvent.change(inputB, { target: { files: [fileB] } });

    // Wait until both validations pass and compare button is enabled
    await waitFor(() => {
      const compareBtn = screen.getByRole('button', {
        name: /compare facial images/i,
      });
      expect(compareBtn).not.toBeDisabled();
    });
  };

  it('immediately enters progress state when Compare is clicked and keeps result hidden during inference', async () => {
    let resolveApi: (value: ComparisonResponse) => void = () => {};
    const pendingPromise = new Promise<ComparisonResponse>((resolve) => {
      resolveApi = resolve;
    });
    vi.mocked(api.compareImagesApi).mockReturnValue(pendingPromise);

    render(
      <ComparisonWorkspace onAddHistory={vi.fn()} onShowToast={vi.fn()} />
    );

    await uploadTestFiles();

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });
    fireEvent.click(compareBtn);

    // Progress card appears immediately
    expect(
      screen.getByText(/BIOMETRIC INFERENCE PIPELINE ACTIVE/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole('progressbar')
    ).toBeInTheDocument();

    // The final ResultPanel must NOT be in the DOM yet
    expect(screen.queryByText(/Raw Cosine Similarity/i)).not.toBeInTheDocument();

    // Compare button is disabled during comparison
    expect(compareBtn).toBeDisabled();
    expect(screen.getByText(/Evaluating Pair\.\.\./i)).toBeInTheDocument();

    // Resolve the real response
    await act(async () => {
      resolveApi(mockComparisonResponse);
    });

    // Progress moves to completion and ResultPanel is revealed
    await waitFor(
      () => {
        expect(
          screen.getByText(/Raw Cosine Similarity/i)
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Verified real score rendered
    expect(screen.getAllByText(/\+0\.7421/i).length).toBeGreaterThanOrEqual(1);
  });

  it('prevents duplicate requests when Compare button is clicked multiple times', async () => {
    let resolveApi: (value: ComparisonResponse) => void = () => {};
    const pendingPromise = new Promise<ComparisonResponse>((resolve) => {
      resolveApi = resolve;
    });
    vi.mocked(api.compareImagesApi).mockReturnValue(pendingPromise);

    render(
      <ComparisonWorkspace onAddHistory={vi.fn()} onShowToast={vi.fn()} />
    );

    await uploadTestFiles();

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });

    // Multiple rapid clicks
    fireEvent.click(compareBtn);
    fireEvent.click(compareBtn);
    fireEvent.click(compareBtn);

    expect(api.compareImagesApi).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveApi(mockComparisonResponse);
    });
  });

  it('hides previous result immediately upon triggering a new comparison', async () => {
    vi.mocked(api.compareImagesApi).mockResolvedValue(mockComparisonResponse);

    render(
      <ComparisonWorkspace onAddHistory={vi.fn()} onShowToast={vi.fn()} />
    );

    await uploadTestFiles();

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });
    fireEvent.click(compareBtn);

    // Wait for first comparison result
    await waitFor(
      () => {
        expect(
          screen.getByText(/Raw Cosine Similarity/i)
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Now start second run with a pending promise
    let resolveSecond: (value: ComparisonResponse) => void = () => {};
    const pendingSecond = new Promise<ComparisonResponse>((resolve) => {
      resolveSecond = resolve;
    });
    vi.mocked(api.compareImagesApi).mockReturnValue(pendingSecond);

    fireEvent.click(compareBtn);

    // Previous ResultPanel must immediately be hidden
    expect(screen.queryByText(/Raw Cosine Similarity/i)).not.toBeInTheDocument();
    // Active progress must be visible
    expect(
      screen.getByText(/BIOMETRIC INFERENCE PIPELINE ACTIVE/i)
    ).toBeInTheDocument();

    await act(async () => {
      resolveSecond(mockComparisonResponse);
    });
  });

  it('handles backend error rejection, shows structured error state, and allows retry', async () => {
    vi.mocked(api.compareImagesApi).mockRejectedValueOnce(
      new Error('No face detected in Image A (Probe). Please provide an image with a clearly visible human face.')
    );

    render(
      <ComparisonWorkspace onAddHistory={vi.fn()} onShowToast={vi.fn()} />
    );

    await uploadTestFiles();

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });
    fireEvent.click(compareBtn);

    // Wait for error state
    await waitFor(() => {
      expect(
        screen.getByText(/BIOMETRIC EVALUATION HALTED/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/No face detected in Image A \(Probe\)/i)
      ).toBeInTheDocument();
    });

    // Result panel must NEVER be revealed on error
    expect(screen.queryByText(/Raw Cosine Similarity/i)).not.toBeInTheDocument();

    // Mock success on retry
    vi.mocked(api.compareImagesApi).mockResolvedValueOnce(mockComparisonResponse);

    const retryBtn = screen.getByRole('button', {
      name: /retry comparison evaluation/i,
    });
    fireEvent.click(retryBtn);

    // Fresh request triggered
    expect(api.compareImagesApi).toHaveBeenCalledTimes(2);

    await waitFor(
      () => {
        expect(
          screen.getByText(/Raw Cosine Similarity/i)
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('disables slot actions during active inference and resets state on workspace reset', async () => {
    let resolveApi: (value: ComparisonResponse) => void = () => {};
    const pendingPromise = new Promise<ComparisonResponse>((resolve) => {
      resolveApi = resolve;
    });
    vi.mocked(api.compareImagesApi).mockReturnValue(pendingPromise);

    render(
      <ComparisonWorkspace onAddHistory={vi.fn()} onShowToast={vi.fn()} />
    );

    await uploadTestFiles();

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });
    fireEvent.click(compareBtn);

    // Swap and Reset buttons are disabled while comparing
    const swapBtn = screen.getByRole('button', { name: /swap roles/i });
    const resetBtn = screen.getByRole('button', { name: /^reset$/i });
    expect(swapBtn).toBeDisabled();
    expect(resetBtn).toBeDisabled();

    // Dismiss active progress view
    const dismissBtn = screen.getByRole('button', { name: /dismiss progress view/i });
    fireEvent.click(dismissBtn);

    // Progress view dismissed, workspace returned to idle
    expect(
      screen.queryByText(/BIOMETRIC INFERENCE PIPELINE ACTIVE/i)
    ).not.toBeInTheDocument();
    expect(compareBtn).not.toBeDisabled();

    // Resolve deferred promise
    await act(async () => {
      resolveApi(mockComparisonResponse);
    });
  });
});
