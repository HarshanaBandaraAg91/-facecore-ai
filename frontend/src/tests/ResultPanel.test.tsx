import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ResultPanel } from '../components/comparison/ResultPanel';
import type { ComparisonResponse } from '../types';

const mockRealResult: ComparisonResponse = {
  status: 'evaluation_completed',
  similarity_score: 0.7421,
  raw_cosine_similarity: 0.7421,
  transformed_display_score: 87.1,
  provisional_threshold: 0.363,
  is_match: true,
  threshold_notice: 'PROVISIONAL UNCALIBRATED BASELINE',
  inference_latency_ms: 12.4,
  timestamp: '2026-10-26T22:00:00Z',
  engine: {
    engine_id: 'opencv-sface-yunet-v1',
    name: 'OpenCV YuNet + SFace Engine',
    version: '2021dec-sface',
    status: 'active',
    is_mock_data: false,
    description: 'Real facial detector (YuNet) and recognizer (SFace)',
    supported_models: ['YuNet-2023mar', 'SFace-2021dec'],
    embedding_dimension: 128,
    inference_device: 'CPU',
    preprocessing_details: 'YuNet 5-point landmark detection and affine alignment to 112x112 RGB tensor.',
    weights_license: 'Apache-2.0 (OpenCV Model Zoo)',
  },
  image_a_diagnostics: {
    filename: 'probe.jpg',
    format: 'JPEG',
    color_mode: 'RGB',
    width: 320,
    height: 320,
    aspect_ratio: '1:1 (Square)',
    file_size_bytes: 45000,
    sha256_hash: 'a1b2c3d4e5f60718293a',
    estimated_sharpness: 92.5,
    contrast_std: 42.1,
    brightness_mean: 135.0,
    resolution_category: 'Standard Definition',
    passes_quality_check: true,
    warnings: [],
    face_detected: true,
    face_count: 1,
    face_confidence: 0.985,
    face_bounding_box: [50, 40, 220, 240],
  },
  image_b_diagnostics: {
    filename: 'reference.jpg',
    format: 'JPEG',
    color_mode: 'RGB',
    width: 320,
    height: 320,
    aspect_ratio: '1:1 (Square)',
    file_size_bytes: 48000,
    sha256_hash: 'f9e8d7c6b5a413243546',
    estimated_sharpness: 88.0,
    contrast_std: 40.5,
    brightness_mean: 130.0,
    resolution_category: 'Standard Definition',
    passes_quality_check: true,
    warnings: [],
    face_detected: true,
    face_count: 1,
    face_confidence: 0.972,
    face_bounding_box: [52, 44, 216, 236],
  },
  interpretation_notice:
    'SFace cosine score of +0.7421 (transformed display index: 87.1/100). The provisional baseline threshold of 0.363 is uncalibrated on this operational distribution and must not be used for identity claims.',
  ethical_disclaimer:
    'RESEARCH EVALUATION ONLY: Facial embedding similarity is an experimental metric and is NOT proof of identity.',
};

describe('ResultPanel Component (Step 02 Real Engine)', () => {
  it('renders raw cosine similarity and normalized display index', () => {
    render(<ResultPanel result={mockRealResult} onClear={vi.fn()} />);

    // Raw cosine similarity
    expect(screen.getAllByText(/\+0\.7421/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Raw Cosine Similarity/i)).toBeInTheDocument();

    // Normalized display score
    expect(screen.getAllByText(/87\.1/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Transformed Display Index/i)).toBeInTheDocument();
  });

  it('renders experimental threshold disclaimer and prevents definitive identity claims', () => {
    render(<ResultPanel result={mockRealResult} onClear={vi.fn()} />);

    // Experimental threshold indicator
    expect(screen.getByText(/PROVISIONAL MATCH \(EXPERIMENTAL BASELINE\)/i)).toBeInTheDocument();
    expect(screen.getByText(/UNCALIBRATED THRESHOLD/i)).toBeInTheDocument();

    // Ethical guardrail banner
    expect(
      screen.getByText(/Cosine Similarity Is Not a Match Probability/i)
    ).toBeInTheDocument();
  });

  it('renders engine telemetry including 128-d dimension and CPU device', () => {
    render(<ResultPanel result={mockRealResult} onClear={vi.fn()} />);

    expect(screen.getByText(/128-d Hyperspherical Vector/i)).toBeInTheDocument();
    expect(screen.getByText(/12\.4 ms/i)).toBeInTheDocument();
    expect(screen.getByText(/WEIGHTS LICENSE: Apache-2.0/i)).toBeInTheDocument();
  });

  it('renders face localization details and bounding box telemetry', () => {
    render(<ResultPanel result={mockRealResult} onClear={vi.fn()} />);

    // Probe face telemetry
    expect(screen.getByText(/98\.5%/i)).toBeInTheDocument();
    // Reference face telemetry
    expect(screen.getByText(/97\.2%/i)).toBeInTheDocument();
  });
});
