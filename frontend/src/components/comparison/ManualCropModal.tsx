import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Crop, X, Check, RotateCcw, Crosshair } from 'lucide-react';


interface ManualCropModalProps {
  isOpen: boolean;
  onClose: () => void;
  imageUrl: string;
  imageWidth: number;
  imageHeight: number;
  initialCropBox?: [number, number, number, number] | null;
  onApplyCrop: (cropBox: [number, number, number, number]) => void;
}

export const ManualCropModal: React.FC<ManualCropModalProps> = ({
  isOpen,
  onClose,
  imageUrl,
  imageWidth,
  imageHeight,
  initialCropBox,
  onApplyCrop,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  // Default to a centered 60% box if no initial crop
  const defaultCrop = useCallback((): [number, number, number, number] => {
    if (initialCropBox && initialCropBox.length === 4) {
      return initialCropBox;
    }
    const cw = Math.max(32, Math.round(imageWidth * 0.6));
    const ch = Math.max(32, Math.round(imageHeight * 0.6));
    const cx = Math.max(0, Math.round((imageWidth - cw) / 2));
    const cy = Math.max(0, Math.round((imageHeight - ch) / 2));
    return [cx, cy, cw, ch];
  }, [imageWidth, imageHeight, initialCropBox]);

  const [crop, setCrop] = useState<[number, number, number, number]>(defaultCrop());
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    if (isOpen) {
      setCrop(defaultCrop());
    }
  }, [isOpen, defaultCrop]);

  if (!isOpen) return null;

  const [cx, cy, cw, ch] = crop;

  // Convert mouse event client coordinates to image coordinate space
  const getImageCoordinates = (e: React.MouseEvent<HTMLDivElement>): { x: number; y: number } | null => {
    if (!imgRef.current) return null;
    const rect = imgRef.current.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return null;

    const scaleX = imageWidth / rect.width;
    const scaleY = imageHeight / rect.height;

    const relX = Math.max(0, Math.min(rect.width, e.clientX - rect.left));
    const relY = Math.max(0, Math.min(rect.height, e.clientY - rect.top));

    return {
      x: Math.round(relX * scaleX),
      y: Math.round(relY * scaleY),
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    const coords = getImageCoordinates(e);
    if (!coords) return;
    setIsDragging(true);
    setDragStart(coords);
    setCrop([coords.x, coords.y, 16, 16]);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging || !dragStart) return;
    const current = getImageCoordinates(e);
    if (!current) return;

    const x1 = Math.min(dragStart.x, current.x);
    const y1 = Math.min(dragStart.y, current.y);
    const x2 = Math.max(dragStart.x, current.x);
    const y2 = Math.max(dragStart.y, current.y);

    const w = Math.max(16, Math.min(imageWidth - x1, x2 - x1));
    const h = Math.max(16, Math.min(imageHeight - y1, y2 - y1));

    setCrop([x1, y1, w, h]);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDragStart(null);
  };

  const handleResetToCenter = () => {
    const cw = Math.max(32, Math.round(imageWidth * 0.6));
    const ch = Math.max(32, Math.round(imageHeight * 0.6));
    const x = Math.max(0, Math.round((imageWidth - cw) / 2));
    const y = Math.max(0, Math.round((imageHeight - ch) / 2));
    setCrop([x, y, cw, ch]);
  };

  const handleApply = () => {
    // Validate final bounds
    const validX = Math.max(0, Math.min(imageWidth - 16, cx));
    const validY = Math.max(0, Math.min(imageHeight - 16, cy));
    const validW = Math.max(16, Math.min(imageWidth - validX, cw));
    const validH = Math.max(16, Math.min(imageHeight - validY, ch));

    onApplyCrop([validX, validY, validW, validH]);
    onClose();
  };

  const leftPct = (cx / imageWidth) * 100;
  const topPct = (cy / imageHeight) * 100;
  const widthPct = (cw / imageWidth) * 100;
  const heightPct = (ch / imageHeight) * 100;

  return (
    <div
      className="crop-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="crop-modal-title"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        className="crop-modal-card"
        style={{
          width: '100%',
          maxWidth: '720px',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border-medium)',
          borderRadius: '10px',
          boxShadow: 'var(--shadow-lg)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '14px 18px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--bg-surface)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Crop size={18} color="var(--crimson-primary)" />
            <h3
              id="crop-modal-title"
              style={{
                margin: 0,
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--text-bright)',
                letterSpacing: '0.3px',
              }}
            >
              MANUAL FACE CROP &amp; REGION RECOVERY
            </h3>
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary btn-sm"
            style={{ padding: '4px 8px', minWidth: 'auto' }}
            aria-label="Close crop modal"
          >
            <X size={15} />
          </button>
        </div>

        {/* Instructions banner */}
        <div
          style={{
            padding: '8px 18px',
            backgroundColor: 'rgba(225, 29, 72, 0.08)',
            borderBottom: '1px solid var(--border-subtle)',
            fontSize: '11px',
            color: 'var(--text-main)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <Crosshair size={14} color="var(--crimson-primary)" />
          <span>
            Click and drag across the image to enclose the subject&apos;s face.
            The backend detector will strictly re-evaluate the cropped region.
          </span>
        </div>

        {/* Interactive canvas / image area */}
        <div
          ref={containerRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          style={{
            position: 'relative',
            backgroundColor: '#000',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '320px',
            maxHeight: '460px',
            overflow: 'hidden',
            userSelect: 'none',
            cursor: isDragging ? 'crosshair' : 'crosshair',
          }}
        >
          <div style={{ position: 'relative', display: 'inline-block' }}>
            <img
              ref={imgRef}
              src={imageUrl}
              alt="Crop target preview"
              style={{
                maxWidth: '100%',
                maxHeight: '440px',
                display: 'block',
                pointerEvents: 'none',
              }}
            />

            {/* Darkened backdrop mask outside crop */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                pointerEvents: 'none',
                boxShadow: `0 0 0 9999px rgba(0, 0, 0, 0.65)`,
                clipPath: `polygon(
                  0% 0%, 0% 100%, 100% 100%, 100% 0%, 0% 0%,
                  ${leftPct}% ${topPct}%,
                  ${leftPct + widthPct}% ${topPct}%,
                  ${leftPct + widthPct}% ${topPct + heightPct}%,
                  ${leftPct}% ${topPct + heightPct}%,
                  ${leftPct}% ${topPct}%
                )`,
              }}
            />

            {/* Active crop boundary rectangle */}
            <div
              style={{
                position: 'absolute',
                left: `${leftPct}%`,
                top: `${topPct}%`,
                width: `${widthPct}%`,
                height: `${heightPct}%`,
                border: '2px solid var(--emerald-primary)',
                boxShadow: '0 0 10px rgba(16, 185, 129, 0.4)',
                pointerEvents: 'none',
              }}
            >
              {/* Corner handles */}
              <div
                style={{
                  position: 'absolute',
                  top: -4,
                  left: -4,
                  width: 8,
                  height: 8,
                  backgroundColor: '#fff',
                  border: '1px solid #000',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  top: -4,
                  right: -4,
                  width: 8,
                  height: 8,
                  backgroundColor: '#fff',
                  border: '1px solid #000',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  bottom: -4,
                  left: -4,
                  width: 8,
                  height: 8,
                  backgroundColor: '#fff',
                  border: '1px solid #000',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  bottom: -4,
                  right: -4,
                  width: 8,
                  height: 8,
                  backgroundColor: '#fff',
                  border: '1px solid #000',
                }}
              />

              {/* Crop label tag */}
              <div
                style={{
                  position: 'absolute',
                  top: 4,
                  left: 4,
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  color: 'var(--emerald-primary)',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '10px',
                  fontWeight: 700,
                }}
              >
                CROP: {cw} &times; {ch} px
              </div>
            </div>
          </div>
        </div>

        {/* Telemetry footer & controls */}
        <div
          style={{
            padding: '12px 18px',
            borderTop: '1px solid var(--border-subtle)',
            backgroundColor: 'var(--bg-surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div
            className="mono-text"
            style={{ fontSize: '11px', color: 'var(--text-muted)' }}
          >
            ORIGIN: <span style={{ color: 'var(--text-bright)' }}>({cx}, {cy})</span> |
            DIMENSIONS: <span style={{ color: 'var(--text-bright)' }}>{cw} &times; {ch} px</span> |
            RATIO: <span style={{ color: 'var(--text-bright)' }}>{(cw / Math.max(1, ch)).toFixed(2)}:1</span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleResetToCenter}
              className="btn btn-secondary btn-sm"
              title="Reset to center region"
            >
              <RotateCcw size={13} />
              <span>Center Box</span>
            </button>
            <button
              onClick={onClose}
              className="btn btn-secondary btn-sm"
            >
              Cancel
            </button>
            <button
              onClick={handleApply}
              className="btn btn-primary btn-sm"
              style={{
                backgroundColor: 'var(--emerald-primary)',
                borderColor: 'var(--emerald-border)',
                color: '#000',
                fontWeight: 600,
              }}
            >
              <Check size={14} />
              <span>Apply &amp; Validate Crop</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
