import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import {
  ComparisonProgress,
  COMPARISON_STAGES,
} from '../components/comparison/ComparisonProgress';

describe('ComparisonProgress Component (Step 03)', () => {
  it('renders all 6 sequential comparison processing stages in order', () => {
    render(
      <ComparisonProgress
        state="processing"
        progressPercent={35}
        currentStageIndex={2}
        onRetry={vi.fn()}
        onDismiss={vi.fn()}
      />
    );

    expect(screen.getByText(/1\. Preparing images/i)).toBeInTheDocument();
    expect(screen.getByText(/2\. Validating facial inputs/i)).toBeInTheDocument();
    expect(screen.getByText(/3\. Detecting and aligning faces/i)).toBeInTheDocument();
    expect(screen.getByText(/4\. Extracting facial embeddings/i)).toBeInTheDocument();
    expect(screen.getByText(/5\. Calculating cosine similarity/i)).toBeInTheDocument();
    expect(screen.getByText(/6\. Preparing results/i)).toBeInTheDocument();

    // Stage 3 (index 2) should be ACTIVE, prior stages DONE, future stages QUEUED
    expect(screen.getByTestId('stage-stage-prep')).toHaveClass('completed');
    expect(screen.getByTestId('stage-stage-validate')).toHaveClass('completed');
    expect(screen.getByTestId('stage-stage-detect')).toHaveClass('active');
    expect(screen.getByTestId('stage-stage-embed')).toHaveClass('pending');
  });

  it('renders bounded progress percentage and progressbar ARIA attributes', () => {
    render(
      <ComparisonProgress
        state="processing"
        progressPercent={42.7}
        currentStageIndex={2}
        onRetry={vi.fn()}
        onDismiss={vi.fn()}
      />
    );

    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuenow', '43');
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');

    expect(screen.getByText('43%')).toBeInTheDocument();
  });

  it('renders completing state with 100% and verification indicators', () => {
    render(
      <ComparisonProgress
        state="completing"
        progressPercent={100}
        currentStageIndex={5}
        onRetry={vi.fn()}
        onDismiss={vi.fn()}
      />
    );

    expect(
      screen.getByText(/INFERENCE VERIFIED — FINALIZING RESULT/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/100% COMPLETE/i)).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();

    // All stages should be marked completed
    COMPARISON_STAGES.forEach((stage) => {
      expect(screen.getByTestId(`stage-${stage.id}`)).toHaveClass('completed');
    });
  });

  it('renders error panel with retry action and never displays successful result', () => {
    const onRetryMock = vi.fn();
    const onDismissMock = vi.fn();

    render(
      <ComparisonProgress
        state="error"
        progressPercent={30}
        currentStageIndex={2}
        errorMessage="No face detected in Image A (Probe). Please provide an image with a clearly visible human face."
        onRetry={onRetryMock}
        onDismiss={onDismissMock}
      />
    );

    expect(screen.getByText(/BIOMETRIC EVALUATION HALTED/i)).toBeInTheDocument();
    expect(
      screen.getByText(/No face detected in Image A \(Probe\)/i)
    ).toBeInTheDocument();

    const retryBtn = screen.getByRole('button', { name: /retry comparison evaluation/i });
    expect(retryBtn).toBeInTheDocument();
    fireEvent.click(retryBtn);
    expect(onRetryMock).toHaveBeenCalledTimes(1);

    const dismissBtn = screen.getByRole('button', {
      name: /dismiss and return to image selection/i,
    });
    expect(dismissBtn).toBeInTheDocument();
    fireEvent.click(dismissBtn);
    expect(onDismissMock).toHaveBeenCalledTimes(1);
  });

  it('includes accessibility attributes and scientific transparency disclosure', () => {
    render(
      <ComparisonProgress
        state="processing"
        progressPercent={60}
        currentStageIndex={3}
        onRetry={vi.fn()}
        onDismiss={vi.fn()}
      />
    );

    const statusRegion = screen.getByRole('status');
    expect(statusRegion).toHaveAttribute('aria-live', 'polite');
    expect(statusRegion).toHaveAttribute(
      'aria-label',
      'Facial Comparison Processing Status'
    );

    expect(
      screen.getByText(/STAGED CLIENT WORKFLOW/i)
    ).toBeInTheDocument();
  });
});
