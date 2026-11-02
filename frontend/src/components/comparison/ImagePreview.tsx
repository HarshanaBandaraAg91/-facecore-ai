import React from 'react';
import { RefreshCw, Trash2, ShieldCheck, AlertTriangle, Crop, RotateCcw } from 'lucide-react';
import type { ImageQualityDiagnostics } from '../../types';
import { FaceBoundingBoxOverlay } from './FaceBoundingBoxOverlay';

interface ImagePreviewProps {
  previewUrl: string;
  diagnostics: ImageQualityDiagnostics | null;
  onReplace: () => void;
  onRemove: () => void;
  slotLabel: string;
  disabled?: boolean;
  selectedFaceIndex?: number | null;
  onSelectFace?: (index: number) => void;
  onOpenCrop?: () => void;
  onResetCrop?: () => void;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  previewUrl,
  diagnostics,
  onReplace,
  onRemove,
  slotLabel,
  disabled = false,
  selectedFaceIndex,
  onSelectFace,
  onOpenCrop,
  onResetCrop,
}) => {
  const faceCount = diagnostics?.face_count ?? 0;
  const isCropped = Boolean(diagnostics?.crop_bounding_box);

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
          {isCropped && diagnostics?.crop_bounding_box && (
            <span
              style={{
                marginLeft: '8px',
                color: 'var(--amber-primary)',
                borderLeft: '1px solid var(--border-subtle)',
                paddingLeft: '6px',
              }}
            >
              CROP ACTIVE
            </span>
          )}
        </div>

        {diagnostics && (
          <div
            className="hud-tag"
            style={{
              borderColor:
                faceCount === 0
                  ? 'var(--crimson-border)'
                  : faceCount > 1
                  ? 'var(--amber-border)'
                  : diagnostics.passes_quality_check
                  ? 'var(--emerald-border)'
                  : 'var(--amber-border)',
              color:
                faceCount === 0
                  ? 'var(--crimson-primary)'
                  : faceCount > 1
                  ? 'var(--amber-primary)'
                  : diagnostics.passes_quality_check
                  ? 'var(--emerald-primary)'
                  : 'var(--amber-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            {faceCount === 0 ? (
              <>
                <AlertTriangle size={12} />
                <span>NO FACE DETECTED</span>
              </>
            ) : faceCount > 1 ? (
              <>
                <AlertTriangle size={12} />
                <span>{faceCount} FACES FOUND</span>
              </>
            ) : diagnostics.passes_quality_check ? (
              <>
                <ShieldCheck size={12} />
                <span>1 FACE VALIDATED</span>
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

      {/* Main image with bounding box overlay wrapper */}
      <div style={{ position: 'relative', display: 'inline-block' }}>
        <img
          src={previewUrl}
          alt={`Preview for ${slotLabel}`}
          className="preview-img"
        />

        {diagnostics && diagnostics.detected_faces && diagnostics.detected_faces.length > 0 && onSelectFace && (
          <FaceBoundingBoxOverlay
            faces={diagnostics.detected_faces}
            imageWidth={diagnostics.width}
            imageHeight={diagnostics.height}
            selectedFaceIndex={selectedFaceIndex}
            onSelectFace={onSelectFace}
            disabled={disabled}
          />
        )}
      </div>

      {/* Bottom action buttons */}
      <div className="preview-controls">
        {onOpenCrop && (
          <button
            onClick={onOpenCrop}
            disabled={disabled}
            className="btn btn-secondary btn-sm"
            title="Crop face region"
            aria-label="Crop face region"
          >
            <Crop size={13} />
            <span>{isCropped ? 'Edit Crop' : 'Crop Face'}</span>
          </button>
        )}

        {isCropped && onResetCrop && (
          <button
            onClick={onResetCrop}
            disabled={disabled}
            className="btn btn-secondary btn-sm"
            title="Reset crop to full image"
            aria-label="Reset crop"
          >
            <RotateCcw size={13} />
            <span>Full Image</span>
          </button>
        )}

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

