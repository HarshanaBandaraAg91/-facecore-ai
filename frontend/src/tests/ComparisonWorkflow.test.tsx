import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  ComparisonWorkspace,
  TARGET_VISUAL_PROGRESS_DURATION_MS,
} from '../components/comparison/ComparisonWorkspace';
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

describe('Comparison Workflow & Staged Progress Machine (Step 03.1)', () => {
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
    vi.useRealTimers();
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

    await act(async () => {
      fireEvent.change(inputA, { target: { files: [fileA] } });
      fireEvent.change(inputB, { target: { files: [fileB] } });
    });

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });
    expect(compareBtn).not.toBeDisabled();
  };

  it('renders progress component directly below Execute Comparison, outside ResultPanel', async () => {
    vi.mocked(api.compareImagesApi).mockReturnValue(new Promise(() => {}));

    render(
      <ComparisonWorkspace onAddHistory={vi.fn()} onShowToast={vi.fn()} />
    );
    await uploadTestFiles();

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });
    fireEvent.click(compareBtn);

    // Progress card is present directly below compare action section
    const progressCard = screen.getByRole('status');
    expect(progressCard).toBeInTheDocument();
    expect(progressCard).toHaveClass('comparison-progress-card');

    // ResultPanel is NOT rendered
    expect(screen.queryByText(/Biometric Evaluation Outcome/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Raw Cosine Similarity/i)).not.toBeInTheDocument();
  });

  it('immediately enters progress state when Compare is clicked and starts at initial percent', async () => {
    vi.mocked(api.compareImagesApi).mockReturnValue(new Promise(() => {}));

    render(
      <ComparisonWorkspace onAddHistory={vi.fn()} onShowToast={vi.fn()} />
    );
    await uploadTestFiles();

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });
    fireEvent.click(compareBtn);

    expect(
      screen.getByText(/BIOMETRIC INFERENCE PIPELINE ACTIVE/i)
    ).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(compareBtn).toBeDisabled();
    expect(screen.getByText(/Evaluating Pair\.\.\./i)).toBeInTheDocument();
  });

  it('a successful fast response still waits for approximately 5 seconds of visible progress before final reveal', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date', 'performance'] });
    // Fast response (e.g. 25ms in reality)
    vi.mocked(api.compareImagesApi).mockResolvedValue(mockComparisonResponse);

    render(
      <ComparisonWorkspace onAddHistory={vi.fn()} onShowToast={vi.fn()} />
    );
    await uploadTestFiles();

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });
    fireEvent.click(compareBtn);

    // Immediately in progress
    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    // Fast-forward 2500ms (halfway through the 5-second minimum duration)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500);
    });

    // Still processing! Progress bar is active, percentage is under 100%, and ResultPanel is NOT yet revealed
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    const progressVal = Number(screen.getByRole('progressbar').getAttribute('aria-valuenow'));
    expect(progressVal).toBeGreaterThanOrEqual(30);
    expect(progressVal).toBeLessThan(100);
    expect(screen.queryByText(/Raw Cosine Similarity/i)).not.toBeInTheDocument();

    // Fast-forward past the 5-second mark (total 5050ms)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2550);
    });

    // Completing state reached (100%)
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');

    // Advance completion delay (350ms)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(350);
    });

    // Progress component is completely UNMOUNTED after success
    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    expect(screen.queryByText(/BIOMETRIC INFERENCE PIPELINE ACTIVE/i)).not.toBeInTheDocument();

    // Real ResultPanel is revealed in its place directly below button
    expect(screen.getByText(/Raw Cosine Similarity/i)).toBeInTheDocument();
    expect(screen.getAllByText(/\+0\.7421/i).length).toBeGreaterThanOrEqual(1);
  });

  it('a slower backend response delays final reveal until the real response arrives', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date', 'performance'] });
    let resolveApi: (value: ComparisonResponse) => void = () => {};
    const slowPromise = new Promise<ComparisonResponse>((resolve) => {
      resolveApi = resolve;
    });
    vi.mocked(api.compareImagesApi).mockReturnValue(slowPromise);

    render(
      <ComparisonWorkspace onAddHistory={vi.fn()} onShowToast={vi.fn()} />
    );
    await uploadTestFiles();

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });
    fireEvent.click(compareBtn);

    // Fast-forward 5000ms (visual duration elapsed, but API response NOT arrived yet)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });

    // Progress bar must NOT show 100% because real API response has not completed!
    const progressVal = Number(screen.getByRole('progressbar').getAttribute('aria-valuenow'));
    expect(progressVal).toBeLessThanOrEqual(92);
    expect(screen.queryByText(/Raw Cosine Similarity/i)).not.toBeInTheDocument();

    // Now resolve API response at t=5500ms
    await act(async () => {
      resolveApi(mockComparisonResponse);
      await vi.advanceTimersByTimeAsync(100);
    });

    // Now progress reaches 100%
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '100');

    // Advance completion delay (350ms)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(350);
    });

    // Result is now revealed
    expect(screen.getByText(/Raw Cosine Similarity/i)).toBeInTheDocument();
  });

  it('backend errors appear promptly without waiting 5 seconds and never reveal successful results', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date', 'performance'] });
    vi.mocked(api.compareImagesApi).mockRejectedValue(
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

    // Advance a tiny fraction of time (~100ms, FAR below 5 seconds)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(100);
    });

    // Error is displayed promptly without waiting 5 seconds!
    expect(
      screen.getByText(/BIOMETRIC EVALUATION HALTED/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No face detected in Image A \(Probe\)/i)
    ).toBeInTheDocument();

    // ResultPanel must NEVER be shown
    expect(screen.queryByText(/Raw Cosine Similarity/i)).not.toBeInTheDocument();
  });

  it('prevents duplicate requests when Compare button is clicked multiple times', async () => {
    vi.mocked(api.compareImagesApi).mockReturnValue(new Promise(() => {}));

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
  });

  it('hides previous result immediately upon triggering a new comparison', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval', 'Date', 'performance'] });
    vi.mocked(api.compareImagesApi).mockResolvedValue(mockComparisonResponse);

    render(
      <ComparisonWorkspace onAddHistory={vi.fn()} onShowToast={vi.fn()} />
    );
    await uploadTestFiles();

    const compareBtn = screen.getByRole('button', {
      name: /compare facial images/i,
    });
    fireEvent.click(compareBtn);

    // Advance through first run (5000ms + 350ms)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(TARGET_VISUAL_PROGRESS_DURATION_MS + 400);
    });

    // ResultPanel is visible
    expect(screen.getByText(/Raw Cosine Similarity/i)).toBeInTheDocument();

    // Start a second run with a pending promise
    vi.mocked(api.compareImagesApi).mockReturnValue(new Promise(() => {}));
    fireEvent.click(compareBtn);

    // Previous ResultPanel must IMMEDIATELY be hidden
    expect(screen.queryByText(/Raw Cosine Similarity/i)).not.toBeInTheDocument();
    // Active progress must be visible
    expect(
      screen.getByText(/BIOMETRIC INFERENCE PIPELINE ACTIVE/i)
    ).toBeInTheDocument();
  });

  it('disables slot actions during active inference and resets state on workspace reset', async () => {
    vi.mocked(api.compareImagesApi).mockReturnValue(new Promise(() => {}));

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
  });
});
