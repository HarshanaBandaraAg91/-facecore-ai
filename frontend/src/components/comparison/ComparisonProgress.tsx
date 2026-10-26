import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ShieldAlert,
  RotateCcw,
  X,
  Layers,
  Info,
} from 'lucide-react';
import type { ComparisonProcessingState, ComparisonStageInfo } from '../../types';

export const COMPARISON_STAGES: readonly ComparisonStageInfo[] = [
  {
    id: 'stage-prep',
    label: 'Preparing images',
    detail: 'Cryptographic hashing, byte array conversion, and pre-flight validation',
  },
  {
    id: 'stage-validate',
    label: 'Validating facial inputs',
    detail: 'Checking image dimensions, RGB color space, and memory safety boundaries',
  },
  {
    id: 'stage-detect',
    label: 'Detecting and aligning faces',
    detail: 'Executing YuNet edge CNN and 5-point landmark regression',
  },
  {
    id: 'stage-embed',
    label: 'Extracting facial embeddings',
    detail: 'Generating 128-dimensional unit feature vector via SFace (SphereFace2)',
  },
  {
    id: 'stage-cosine',
    label: 'Calculating cosine similarity',
    detail: 'Computing hyperspherical dot product and angular distance theta',
  },
  {
    id: 'stage-results',
    label: 'Preparing results',
    detail: 'Compiling diagnostics, quality advisories, and display score projection',
  },
] as const;

export interface ComparisonProgressProps {
  state: ComparisonProcessingState;
  progressPercent: number;
  currentStageIndex: number;
  errorMessage?: string | null;
  onRetry: () => void;
  onDismiss: () => void;
}

export const ComparisonProgress: React.FC<ComparisonProgressProps> = ({
  state,
  progressPercent,
  currentStageIndex,
  errorMessage,
  onRetry,
  onDismiss,
}) => {
  const isCompleting = state === 'completing' || state === 'success';
  const isError = state === 'error';
  const boundedPercent = Math.min(100, Math.max(0, Math.round(progressPercent)));

  const currentStage = COMPARISON_STAGES[currentStageIndex] ?? COMPARISON_STAGES[0];

  return (
    <div
      className={`card comparison-progress-card ${
        isCompleting
          ? 'is-completing'
          : isError
          ? 'is-error'
          : 'is-processing'
      }`}
      role="status"
      aria-live="polite"
      aria-label="Facial Comparison Processing Status"
    >
      {/* Top Header */}
      <div className="progress-card-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isError ? (
            <ShieldAlert size={18} color="var(--crimson-primary)" />
          ) : isCompleting ? (
            <CheckCircle2 size={18} color="var(--emerald-primary)" />
          ) : (
            <Layers size={18} color="var(--crimson-primary)" />
          )}
          <span style={{ fontWeight: 600, fontSize: '13px', color: 'var(--text-bright)' }}>
            {isError
              ? 'BIOMETRIC EVALUATION HALTED'
              : isCompleting
              ? 'INFERENCE VERIFIED — FINALIZING RESULT'
              : 'BIOMETRIC INFERENCE PIPELINE ACTIVE'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            className={`badge-tag ${
              isError ? 'crimson' : isCompleting ? 'emerald' : 'cyan'
            }`}
            style={{ fontSize: '10px' }}
          >
            {isError
              ? 'PIPELINE ERROR'
              : isCompleting
              ? '100% COMPLETE'
              : 'LOCAL CPU PIPELINE'}
          </span>
          <button
            onClick={onDismiss}
            className="btn btn-secondary btn-sm"
            style={{ padding: '4px 8px' }}
            title="Dismiss progress view"
            aria-label="Dismiss progress view"
          >
            <X size={13} />
          </button>
        </div>
      </div>

      {/* Progress Track & Numeric Counter */}
      <div className="progress-track-wrapper">
        <div className="progress-numeric-row">
          <div>
            <span
              style={{
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-dim)',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
              }}
            >
              Current Operation
            </span>
            <div
              style={{
                fontSize: '13px',
                fontWeight: 600,
                color: isError
                  ? '#fda4af'
                  : isCompleting
                  ? 'var(--emerald-primary)'
                  : 'var(--text-bright)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                marginTop: '2px',
              }}
            >
              {!isError && !isCompleting && (
                <Loader2 size={13} className="spin-icon" color="var(--crimson-primary)" />
              )}
              <span>
                {isError
                  ? 'Execution interrupted'
                  : isCompleting
                  ? 'Evaluation finalized'
                  : currentStage.label}
              </span>
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span
              className="mono-text"
              style={{
                fontSize: '24px',
                fontWeight: 700,
                color: isError
                  ? 'var(--crimson-primary)'
                  : isCompleting
                  ? 'var(--emerald-primary)'
                  : 'var(--text-bright)',
              }}
            >
              {boundedPercent}%
            </span>
            <div
              style={{
                fontSize: '10px',
                color: 'var(--text-dim)',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {isCompleting ? 'VERIFIED' : 'ESTIMATED'}
            </div>
          </div>
        </div>

        {/* The Bar */}
        <div
          className="progress-track"
          role="progressbar"
          aria-valuenow={boundedPercent}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            className={`progress-fill ${
              isCompleting ? 'completing' : isError ? 'error' : ''
            }`}
            style={{ width: `${boundedPercent}%` }}
          >
            {!isError && <div className="scanline-sweep" />}
          </div>
        </div>
      </div>

      {/* Error Panel if Error occurred */}
      {isError && (
        <div className="progress-error-container">
          <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <AlertTriangle
              size={20}
              color="var(--crimson-primary)"
              style={{ flexShrink: 0, marginTop: '2px' }}
            />
            <div style={{ flex: 1 }}>
              <div
                style={{
                  fontWeight: 600,
                  fontSize: '13px',
                  color: 'var(--text-bright)',
                  marginBottom: '4px',
                }}
              >
                Inference Evaluation Rejected by Engine
              </div>
              <p
                style={{
                  fontSize: '12px',
                  color: '#fecdd3',
                  lineHeight: '1.5',
                  marginBottom: '12px',
                }}
              >
                {errorMessage ||
                  'The comparison request failed. Please ensure both images contain exactly one clear, unobstructed human face.'}
              </p>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <button
                  onClick={onRetry}
                  className="btn btn-primary btn-sm"
                  aria-label="Retry comparison evaluation"
                >
                  <RotateCcw size={13} />
                  <span>Retry Evaluation</span>
                </button>
                <button
                  onClick={onDismiss}
                  className="btn btn-secondary btn-sm"
                  aria-label="Dismiss and return to image selection"
                >
                  <span>Dismiss & Edit Images</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sequential Stages Grid */}
      <div className="stages-grid">
        {COMPARISON_STAGES.map((stage, idx) => {
          let stageStatus: 'completed' | 'active' | 'pending' = 'pending';

          if (isCompleting || idx < currentStageIndex) {
            stageStatus = 'completed';
          } else if (idx === currentStageIndex && !isError) {
            stageStatus = 'active';
          } else if (idx === currentStageIndex && isError) {
            stageStatus = 'active';
          }

          return (
            <div
              key={stage.id}
              className={`stage-item ${stageStatus}`}
              data-testid={`stage-${stage.id}`}
            >
              <div style={{ flexShrink: 0, marginTop: '2px' }}>
                {stageStatus === 'completed' ? (
                  <CheckCircle2 size={15} color="var(--emerald-primary)" />
                ) : stageStatus === 'active' ? (
                  isError ? (
                    <AlertTriangle size={15} color="var(--crimson-primary)" />
                  ) : (
                    <Loader2
                      size={15}
                      className="spin-icon"
                      color="var(--crimson-primary)"
                    />
                  )
                ) : (
                  <div className="stage-dot pending" />
                )}
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    color:
                      stageStatus === 'completed'
                        ? 'var(--emerald-primary)'
                        : stageStatus === 'active'
                        ? isError
                          ? '#fda4af'
                          : 'var(--text-bright)'
                        : 'var(--text-muted)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span>
                    {idx + 1}. {stage.label}
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '9px',
                      textTransform: 'uppercase',
                      color:
                        stageStatus === 'completed'
                          ? 'var(--emerald-primary)'
                          : stageStatus === 'active'
                          ? isError
                            ? 'var(--crimson-primary)'
                            : 'var(--cyan-primary)'
                          : 'var(--text-dim)',
                    }}
                  >
                    {stageStatus === 'completed'
                      ? 'DONE'
                      : stageStatus === 'active'
                      ? isError
                        ? 'HALTED'
                        : 'ACTIVE'
                      : 'QUEUED'}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: '10px',
                    color: 'var(--text-dim)',
                    lineHeight: '1.4',
                    marginTop: '2px',
                  }}
                >
                  {stage.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Scientific Transparency Footer */}
      <div
        style={{
          padding: '10px 16px',
          backgroundColor: 'var(--bg-surface)',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '11px',
          color: 'var(--text-dim)',
          fontFamily: 'var(--font-mono)',
        }}
      >
        <Info size={12} color="var(--text-muted)" style={{ flexShrink: 0 }} />
        <span>
          STAGED CLIENT WORKFLOW // Neural inference executes locally on CPU via OpenCV YuNet (detection) & SFace (128-d recognition). 100% resolution occurs only upon verified HTTP 200 payload.
        </span>
      </div>
    </div>
  );
};
