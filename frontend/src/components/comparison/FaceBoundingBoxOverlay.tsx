import React from 'react';
import { UserCheck, CheckCircle2 } from 'lucide-react';
import type { DetectedFaceSummary } from '../../types';

interface FaceBoundingBoxOverlayProps {
  faces: DetectedFaceSummary[];
  imageWidth: number;
  imageHeight: number;
  selectedFaceIndex: number | null | undefined;
  onSelectFace: (index: number) => void;
  disabled?: boolean;
}

export const FaceBoundingBoxOverlay: React.FC<FaceBoundingBoxOverlayProps> = ({
  faces,
  imageWidth,
  imageHeight,
  selectedFaceIndex,
  onSelectFace,
  disabled = false,
}) => {
  if (!faces || faces.length === 0 || imageWidth <= 0 || imageHeight <= 0) {
    return null;
  }

  // Active index: explicitly selected, or defaults to 0 if multiple faces exist
  const activeIndex = selectedFaceIndex ?? 0;

  return (
    <div
      className="face-bounding-box-overlay"
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
      }}
      aria-label="Detected face bounding boxes"
    >
      {faces.map((face) => {
        const [bx, by, bw, bh] = face.box;
        const leftPct = (bx / imageWidth) * 100;
        const topPct = (by / imageHeight) * 100;
        const widthPct = (bw / imageWidth) * 100;
        const heightPct = (bh / imageHeight) * 100;
        const isSelected = face.index === activeIndex;

        return (
          <div
            key={face.index}
            role="button"
            tabIndex={disabled ? -1 : 0}
            onClick={(e) => {
              e.stopPropagation();
              if (!disabled) onSelectFace(face.index);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.stopPropagation();
                if (!disabled) onSelectFace(face.index);
              }
            }}
            aria-label={`Select Face #${face.index + 1} (Confidence: ${(
              face.confidence * 100
            ).toFixed(1)}%)`}
            aria-pressed={isSelected}
            className={`face-box-reticle ${isSelected ? 'selected-reticle' : 'unselected-reticle'}`}
            style={{
              position: 'absolute',
              left: `${leftPct}%`,
              top: `${topPct}%`,
              width: `${widthPct}%`,
              height: `${heightPct}%`,
              pointerEvents: disabled ? 'none' : 'auto',
              cursor: disabled ? 'default' : 'pointer',
              border: isSelected
                ? '2px solid var(--emerald-primary)'
                : '2px dashed rgba(245, 158, 11, 0.8)',
              boxShadow: isSelected
                ? '0 0 14px rgba(16, 185, 129, 0.6), inset 0 0 10px rgba(16, 185, 129, 0.25)'
                : '0 0 8px rgba(0, 0, 0, 0.6)',
              backgroundColor: isSelected
                ? 'rgba(16, 185, 129, 0.08)'
                : 'rgba(245, 158, 11, 0.04)',
              borderRadius: '3px',
              transition: 'all 0.15s ease-in-out',
            }}
          >
            {/* Corner cybernetic ticks */}
            <div
              style={{
                position: 'absolute',
                top: -3,
                left: -3,
                width: 7,
                height: 7,
                borderTop: isSelected ? '2px solid #fff' : '2px solid var(--amber-primary)',
                borderLeft: isSelected ? '2px solid #fff' : '2px solid var(--amber-primary)',
              }}
            />
            <div
              style={{
                position: 'absolute',
                top: -3,
                right: -3,
                width: 7,
                height: 7,
                borderTop: isSelected ? '2px solid #fff' : '2px solid var(--amber-primary)',
                borderRight: isSelected ? '2px solid #fff' : '2px solid var(--amber-primary)',
              }}
            />
            <div
              style={{
                position: 'absolute',
                bottom: -3,
                left: -3,
                width: 7,
                height: 7,
                borderBottom: isSelected ? '2px solid #fff' : '2px solid var(--amber-primary)',
                borderLeft: isSelected ? '2px solid #fff' : '2px solid var(--amber-primary)',
              }}
            />
            <div
              style={{
                position: 'absolute',
                bottom: -3,
                right: -3,
                width: 7,
                height: 7,
                borderBottom: isSelected ? '2px solid #fff' : '2px solid var(--amber-primary)',
                borderRight: isSelected ? '2px solid #fff' : '2px solid var(--amber-primary)',
              }}
            />

            {/* Floating face index badge */}
            <div
              style={{
                position: 'absolute',
                top: -24,
                left: 0,
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '2px 6px',
                borderRadius: '3px',
                fontFamily: 'var(--font-mono)',
                fontSize: '10px',
                fontWeight: 700,
                letterSpacing: '0.5px',
                whiteSpace: 'nowrap',
                backgroundColor: isSelected ? 'var(--emerald-primary)' : 'rgba(15, 23, 42, 0.9)',
                color: isSelected ? '#000' : 'var(--amber-primary)',
                border: isSelected ? 'none' : '1px solid var(--amber-border)',
                boxShadow: '0 2px 6px rgba(0, 0, 0, 0.6)',
              }}
            >
              {isSelected ? (
                <>
                  <CheckCircle2 size={10} color="#000" />
                  <span>FACE #{face.index + 1} (ACTIVE)</span>
                </>
              ) : (
                <>
                  <UserCheck size={10} color="var(--amber-primary)" />
                  <span>FACE #{face.index + 1} ({(face.confidence * 100).toFixed(0)}%)</span>
                </>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
