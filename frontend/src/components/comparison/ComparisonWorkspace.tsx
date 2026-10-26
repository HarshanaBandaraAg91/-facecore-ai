import React, { useState, useRef, useEffect } from 'react';
import {
  ArrowRightLeft,
  RotateCcw,
  Play,
  Loader2,
  ShieldAlert,
} from 'lucide-react';
import type {
  UploadedImageSlot,
  ComparisonResponse,
  ComparisonHistoryEntry,
  ComparisonProcessingState,
} from '../../types';
import { ImageUploadCard } from './ImageUploadCard';
import { ComparisonProgress } from './ComparisonProgress';
import { ResultPanel } from './ResultPanel';
import { compareImagesApi } from '../../services/api';

interface ComparisonWorkspaceProps {
  onAddHistory: (entry: ComparisonHistoryEntry) => void;
  onShowToast: (msg: {
    type: 'success' | 'error' | 'info' | 'warning';
    message: string;
    title?: string;
  }) => void;
}

/**
 * Intentional visual presentation duration (approx 5.0 seconds).
 * CPU neural inference completes in ~20-35ms, but a minimum 5s visual sequence
 * is maintained so the user can inspect the staged cyber-intelligence verification.
 * The true CPU latency is preserved in response.inference_latency_ms and displayed accurately.
 */
export const TARGET_VISUAL_PROGRESS_DURATION_MS = 5000;

export const ComparisonWorkspace: React.FC<ComparisonWorkspaceProps> = ({
  onAddHistory,
  onShowToast,
}) => {
  const [slotA, setSlotA] = useState<UploadedImageSlot>({
    id: 'probe',
    label: 'IMAGE A (PROBE / QUERY)',
    file: null,
    previewUrl: null,
    diagnostics: null,
    isValidating: false,
    validationError: null,
  });

  const [slotB, setSlotB] = useState<UploadedImageSlot>({
    id: 'reference',
    label: 'IMAGE B (REFERENCE / GALLERY)',
    file: null,
    previewUrl: null,
    diagnostics: null,
    isValidating: false,
    validationError: null,
  });

  // State machine for comparison lifecycle
  const [comparisonState, setComparisonState] =
    useState<ComparisonProcessingState>('idle');
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [currentStageIndex, setCurrentStageIndex] = useState<number>(0);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const [comparisonResult, setComparisonResult] =
    useState<ComparisonResponse | null>(null);

  const currentRequestIdRef = useRef<number>(0);
  const abortControllerRef = useRef<AbortController | null>(null);
  const progressTimerRef = useRef<number | null>(null);
  const completionTimerRef = useRef<number | null>(null);
  const cancelVisualDurationRef = useRef<(() => void) | null>(null);

  const isComparing =
    comparisonState === 'validating' ||
    comparisonState === 'processing' ||
    comparisonState === 'completing';

  // Both images must be loaded, have valid diagnostics, and not have pending validation
  const canCompare =
    Boolean(slotA.file && slotA.diagnostics && !slotA.isValidating && !slotA.validationError) &&
    Boolean(slotB.file && slotB.diagnostics && !slotB.isValidating && !slotB.validationError) &&
    !isComparing;

  // Cleanup timers and abort controllers on unmount
  useEffect(() => {
    return () => {
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
      if (completionTimerRef.current) clearTimeout(completionTimerRef.current);
      cancelVisualDurationRef.current?.();
      abortControllerRef.current?.abort();
    };
  }, []);

  const cancelActiveComparison = () => {
    currentRequestIdRef.current += 1;
    if (progressTimerRef.current) clearInterval(progressTimerRef.current);
    if (completionTimerRef.current) clearTimeout(completionTimerRef.current);
    cancelVisualDurationRef.current?.();
    cancelVisualDurationRef.current = null;
    abortControllerRef.current?.abort();
    setComparisonState('idle');
    setProgressPercent(0);
    setCurrentStageIndex(0);
    setComparisonError(null);
  };

  const handleUpdateSlotA = (updated: Partial<UploadedImageSlot>) => {
    cancelActiveComparison();
    setSlotA((prev) => ({ ...prev, ...updated }));
    setComparisonResult(null);
  };

  const handleUpdateSlotB = (updated: Partial<UploadedImageSlot>) => {
    cancelActiveComparison();
    setSlotB((prev) => ({ ...prev, ...updated }));
    setComparisonResult(null);
  };

  const handleClearSlotA = () => {
    cancelActiveComparison();
    if (slotA.previewUrl) URL.revokeObjectURL(slotA.previewUrl);
    setSlotA({
      id: 'probe',
      label: 'IMAGE A (PROBE / QUERY)',
      file: null,
      previewUrl: null,
      diagnostics: null,
      isValidating: false,
      validationError: null,
    });
    setComparisonResult(null);
  };

  const handleClearSlotB = () => {
    cancelActiveComparison();
    if (slotB.previewUrl) URL.revokeObjectURL(slotB.previewUrl);
    setSlotB({
      id: 'reference',
      label: 'IMAGE B (REFERENCE / GALLERY)',
      file: null,
      previewUrl: null,
      diagnostics: null,
      isValidating: false,
      validationError: null,
    });
    setComparisonResult(null);
  };

  const handleSwapSlots = () => {
    if (isComparing) return;
    cancelActiveComparison();
    const tempA = { ...slotA, label: 'IMAGE A (PROBE / QUERY)', id: 'probe' as const };
    const tempB = { ...slotB, label: 'IMAGE B (REFERENCE / GALLERY)', id: 'reference' as const };
    setSlotA(tempB);
    setSlotB(tempA);
    setComparisonResult(null);
    onShowToast({
      type: 'info',
      message: 'Probe and Reference image slots swapped.',
    });
  };

  const handleResetWorkspace = () => {
    cancelActiveComparison();
    handleClearSlotA();
    handleClearSlotB();
    setComparisonResult(null);
    onShowToast({
      type: 'info',
      message: 'Workspace reset to default state.',
    });
  };

  const handleDismissProgress = () => {
    cancelActiveComparison();
  };

  const handleExecuteComparison = async () => {
    if (!slotA.file || !slotB.file || isComparing) return;

    // Increment request ID and cancel any existing timer/request
    const thisRequestId = ++currentRequestIdRef.current;
    if (progressTimerRef.current) clearInterval(progressTimerRef.current);
    if (completionTimerRef.current) clearTimeout(completionTimerRef.current);
    cancelVisualDurationRef.current?.();
    cancelVisualDurationRef.current = null;
    abortControllerRef.current?.abort();

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    // Immediately enter processing state and hide previous result
    setComparisonResult(null);
    setComparisonError(null);
    setComparisonState('processing');
    setProgressPercent(4);
    setCurrentStageIndex(0);

    const startTime = performance.now();

    // Staged progress ticker advancing smoothly towards ~92% across TARGET_VISUAL_PROGRESS_DURATION_MS
    progressTimerRef.current = window.setInterval(() => {
      if (currentRequestIdRef.current !== thisRequestId) return;
      const elapsed = performance.now() - startTime;
      const progressFraction = Math.min(1, elapsed / TARGET_VISUAL_PROGRESS_DURATION_MS);

      // Smooth progress calculation capping at 92% until both conditions are met
      const targetPercent = Math.min(92, Math.round(4 + progressFraction * 88));
      setProgressPercent((prev) => Math.max(prev, targetPercent));

      // 6 stages evenly distributed across the 5000ms visual timeline (~800ms each)
      setCurrentStageIndex(() => {
        if (elapsed < 750) return 0;
        if (elapsed < 1550) return 1;
        if (elapsed < 2400) return 2;
        if (elapsed < 3250) return 3;
        if (elapsed < 4100) return 4;
        return 5;
      });
    }, 60);

    // Create cancellable visual duration promise (~5000ms)
    let visualDurationTimeout: number = 0;
    const visualDurationPromise = new Promise<void>((resolve) => {
      visualDurationTimeout = window.setTimeout(resolve, TARGET_VISUAL_PROGRESS_DURATION_MS);
      cancelVisualDurationRef.current = () => {
        window.clearTimeout(visualDurationTimeout);
        resolve();
      };
    });

    try {
      const apiPromise = compareImagesApi(slotA.file, slotB.file, abortController.signal);

      // Concurrently wait for BOTH:
      // 1. Real API call completion & validation
      // 2. Minimum visual duration (approx 5.0 seconds)
      // If apiPromise rejects, Promise.all rejects IMMEDIATELY without waiting 5 seconds!
      const [response] = await Promise.all([apiPromise, visualDurationPromise]);

      // Guard against stale or cancelled requests
      if (currentRequestIdRef.current !== thisRequestId) return;
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);

      // Validate response structure before accepting
      if (
        !response ||
        !response.engine ||
        response.raw_cosine_similarity === null ||
        response.raw_cosine_similarity === undefined
      ) {
        throw new Error('Received malformed response payload from evaluation engine.');
      }

      // Both conditions satisfied: Real API complete & validated + 5s visual duration elapsed!
      // Enter completing state: jump visual progress to 100% and activate final stage
      setComparisonState('completing');
      setProgressPercent(100);
      setCurrentStageIndex(5);

      // Brief accessible completion delay before unmounting progress and revealing actual ResultPanel
      completionTimerRef.current = window.setTimeout(() => {
        if (currentRequestIdRef.current !== thisRequestId) return;

        setComparisonResult(response);
        setComparisonState('success');

        // Record metadata-only history entry
        const historyEntry: ComparisonHistoryEntry = {
          id: `eval-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
          timestamp: response.timestamp,
          imageAName: response.image_a_diagnostics.filename,
          imageBName: response.image_b_diagnostics.filename,
          hashAPrefix: response.image_a_diagnostics.sha256_hash,
          hashBPrefix: response.image_b_diagnostics.sha256_hash,
          dimensionsA: `${response.image_a_diagnostics.width}x${response.image_a_diagnostics.height}`,
          dimensionsB: `${response.image_b_diagnostics.width}x${response.image_b_diagnostics.height}`,
          engineName: response.engine.name,
          statusNotice: response.status,
          rawCosineScore: response.raw_cosine_similarity,
          displayScore: response.transformed_display_score,
          isMatch: response.is_match,
        };
        onAddHistory(historyEntry);

        const cosineFormatted =
          response.raw_cosine_similarity !== null && response.raw_cosine_similarity !== undefined
            ? (response.raw_cosine_similarity >= 0 ? '+' : '') + response.raw_cosine_similarity.toFixed(4)
            : 'N/A';

        onShowToast({
          type: 'success',
          title: 'Facial Evaluation Complete',
          message: `Embeddings extracted via ${response.engine.name}. Raw Cosine: ${cosineFormatted}`,
        });
      }, 350);
    } catch (err: unknown) {
      // Clean up visual duration wait immediately on error
      window.clearTimeout(visualDurationTimeout);
      cancelVisualDurationRef.current = null;
      if (progressTimerRef.current) clearInterval(progressTimerRef.current);
      if (currentRequestIdRef.current !== thisRequestId) return;
      if (err instanceof Error && err.name === 'AbortError') return;

      const errMsg =
        err instanceof Error
          ? err.message
          : 'Encountered unexpected error during image comparison.';
      setComparisonError(errMsg);
      setComparisonState('error');

      onShowToast({
        type: 'error',
        title: 'Comparison Rejected',
        message: errMsg,
      });
    }
  };

  return (
    <div>
      {/* Intro banner */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h2 style={{ fontSize: '18px', color: 'var(--text-bright)' }}>
            Biometric Pair Inspection
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Upload two facial images to validate cryptographic integrity, evaluate image
            geometry and clarity, and execute modular inference.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {(slotA.file || slotB.file) && (
            <>
              <button
                onClick={handleSwapSlots}
                disabled={isComparing}
                className="btn btn-secondary btn-sm"
                title="Swap Image A and Image B slots"
              >
                <ArrowRightLeft size={13} />
                <span>Swap Roles</span>
              </button>
              <button
                onClick={handleResetWorkspace}
                disabled={isComparing}
                className="btn btn-secondary btn-sm"
                title="Reset workspace"
              >
                <RotateCcw size={13} />
                <span>Reset</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Dual Upload Grid */}
      <div className="upload-comparison-grid">
        <ImageUploadCard
          slot={slotA}
          onUpdateSlot={handleUpdateSlotA}
          onClearSlot={handleClearSlotA}
          otherSlotFileName={slotB.file?.name}
          disabled={isComparing}
        />
        <ImageUploadCard
          slot={slotB}
          onUpdateSlot={handleUpdateSlotB}
          onClearSlot={handleClearSlotB}
          otherSlotFileName={slotA.file?.name}
          disabled={isComparing}
        />
      </div>

      {/* Central Comparison Control Bar */}
      <div className="compare-action-section">
        <div className="compare-btn-wrapper">
          <button
            onClick={handleExecuteComparison}
            disabled={!canCompare}
            className="btn btn-primary btn-lg compare-btn"
            id="compare-trigger-btn"
            aria-label="Compare facial images"
          >
            {isComparing ? (
              <>
                <Loader2 size={18} className="spin-icon" />
                <span>Evaluating Pair...</span>
              </>
            ) : (
              <>
                <Play size={18} fill="currentColor" />
                <span>Execute Comparison</span>
              </>
            )}
          </button>
        </div>

        {!canCompare && !isComparing && (
          <div
            style={{
              fontSize: '12px',
              color: 'var(--text-dim)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <ShieldAlert size={14} color="var(--amber-primary)" />
            <span>
              {slotA.file && slotB.file
                ? 'Validating inputs before comparison can proceed...'
                : 'Upload and validate both Probe (Image A) and Reference (Image B) to enable evaluation.'}
            </span>
          </div>
        )}
      </div>

      {/* Animated Comparison Progress View (Active or Error) */}
      {comparisonState !== 'idle' && comparisonState !== 'success' && (
        <ComparisonProgress
          state={comparisonState}
          progressPercent={progressPercent}
          currentStageIndex={currentStageIndex}
          errorMessage={comparisonError}
          onRetry={handleExecuteComparison}
          onDismiss={handleDismissProgress}
        />
      )}

      {/* Results Area (Revealed ONLY on validated success) */}
      {comparisonState === 'success' && comparisonResult && (
        <ResultPanel
          result={comparisonResult}
          onClear={() => {
            setComparisonResult(null);
            setComparisonState('idle');
          }}
        />
      )}
    </div>
  );
};
