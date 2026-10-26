import React from 'react';
import { RefreshCw, Trash2, ShieldCheck, AlertTriangle } from 'lucide-react';
import type { ImageQualityDiagnostics } from '../../types';

interface ImagePreviewProps {
  previewUrl: string;
  diagnostics: ImageQualityDiagnostics | null;
  onReplace: () => void;
  onRemove: () => void;
  slotLabel: string;
  disabled?: boolean;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  previewUrl,
  diagnostics,
  onReplace,
  onRemove,
  slotLabel,
  disabled = false,
}) => {
  return (
    <div className="preview-container">
      {/* Top HUD overlay */}
      <div className="preview-hud">
        <div className="hud-tag">
          <span style={{ color: 'var(--crimson-primary)', fontWeight: 700 }}>
            {slotLabel}
          </span>
          {diagnostics && (
            <span style={{ marginLeft: '8px', color: 'var(--text-bright)' }}>
              {diagnostics.width} &times; {diagnostics.height} px
            </span>
          )}
        </div>

        {diagnostics && (
          <div
            className="hud-tag"
            style={{
              borderColor: diagnostics.passes_quality_check
                ? 'var(--emerald-border)'
                : 'var(--amber-border)',
              color: diagnostics.passes_quality_check
                ? 'var(--emerald-primary)'
                : 'var(--amber-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            {diagnostics.passes_quality_check ? (
              <>
                <ShieldCheck size={12} />
                <span>VALIDATED</span>
              </>
            ) : (
              <>
                <AlertTriangle size={12} />
                <span>QUALITY ADVISORY</span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Main image element */}
      <img
        src={previewUrl}
        alt={`Preview for ${slotLabel}`}
        className="preview-img"
      />

      {/* Bottom action buttons */}
      <div className="preview-controls">
        <button
          onClick={onReplace}
          disabled={disabled}
          className="btn btn-secondary btn-sm"
          title="Choose a different image file"
          aria-label="Replace image"
        >
          <RefreshCw size={13} />
          <span>Replace</span>
        </button>
        <button
          onClick={onRemove}
          disabled={disabled}
          className="btn btn-danger btn-sm"
          title="Remove current image"
          aria-label="Remove image"
        >
          <Trash2 size={13} />
          <span>Remove</span>
        </button>
      </div>
    </div>
  );
};
