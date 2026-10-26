import React, { useState } from 'react';
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
} from '../../types';
import { ImageUploadCard } from './ImageUploadCard';
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

  const [isComparing, setIsComparing] = useState(false);
  const [comparisonResult, setComparisonResult] =
    useState<ComparisonResponse | null>(null);

  // Both images must be loaded, have valid diagnostics, and not have pending validation
  const canCompare =
    Boolean(slotA.file && slotA.diagnostics && !slotA.isValidating && !slotA.validationError) &&
    Boolean(slotB.file && slotB.diagnostics && !slotB.isValidating && !slotB.validationError) &&
    !isComparing;

  const handleUpdateSlotA = (updated: Partial<UploadedImageSlot>) => {
    setSlotA((prev) => ({ ...prev, ...updated }));
    setComparisonResult(null);
  };

  const handleUpdateSlotB = (updated: Partial<UploadedImageSlot>) => {
    setSlotB((prev) => ({ ...prev, ...updated }));
    setComparisonResult(null);
  };

  const handleClearSlotA = () => {
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
    handleClearSlotA();
    handleClearSlotB();
    setComparisonResult(null);
    onShowToast({
      type: 'info',
      message: 'Workspace reset to default state.',
    });
  };

  const handleExecuteComparison = async () => {
    if (!slotA.file || !slotB.file) return;

    setIsComparing(true);
    try {
      const response = await compareImagesApi(slotA.file, slotB.file);
      setComparisonResult(response);

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
      };
      onAddHistory(historyEntry);

      onShowToast({
        type: 'success',
        title: 'Technical Checks Complete',
        message: 'Pair differential analysis generated. Inference engine is in modular stub mode.',
      });
    } catch (err: unknown) {
      const errMsg =
        err instanceof Error
          ? err.message
          : 'Encountered unexpected error during image comparison.';
      onShowToast({
        type: 'error',
        title: 'Comparison Rejected',
        message: errMsg,
      });
    } finally {
      setIsComparing(false);
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
                className="btn btn-secondary btn-sm"
                title="Swap Image A and Image B slots"
              >
                <ArrowRightLeft size={13} />
                <span>Swap Roles</span>
              </button>
              <button
                onClick={handleResetWorkspace}
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
        />
        <ImageUploadCard
          slot={slotB}
          onUpdateSlot={handleUpdateSlotB}
          onClearSlot={handleClearSlotB}
          otherSlotFileName={slotA.file?.name}
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

        {!canCompare && (
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

      {/* Results Area */}
      {comparisonResult && (
        <ResultPanel
          result={comparisonResult}
          onClear={() => setComparisonResult(null)}
        />
      )}
    </div>
  );
};
