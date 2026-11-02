import React, { useRef, useState } from 'react';
import {
  UploadCloud,
  FileCheck2,
  AlertCircle,
  Loader2,
  AlertTriangle,
  Crop,
} from 'lucide-react';
import type { UploadedImageSlot } from '../../types';
import { ImagePreview } from './ImagePreview';
import { QualityDiagnostics } from './QualityDiagnostics';
import { FaceSelectionBar } from './FaceSelectionBar';
import { ManualCropModal } from './ManualCropModal';
import { validateImageApi } from '../../services/api';

interface ImageUploadCardProps {
  slot: UploadedImageSlot;
  onUpdateSlot: (updated: Partial<UploadedImageSlot>) => void;
  onClearSlot: () => void;
  otherSlotFileName?: string | null;
  disabled?: boolean;
}

export const ImageUploadCard: React.FC<ImageUploadCardProps> = ({
  slot,
  onUpdateSlot,
  onClearSlot,
  disabled = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isCropModalOpen, setIsCropModalOpen] = useState(false);

  const processFile = async (selectedFile: File) => {
    // Client-side quick sanity check
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(selectedFile.type)) {
      onUpdateSlot({
        file: null,
        previewUrl: null,
        diagnostics: null,
        selectedFaceIndex: null,
        cropBox: null,
        isValidating: false,
        validationError:
          'Unsupported file format. Please upload an authentic JPEG, PNG, or WebP image.',
      });
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      onUpdateSlot({
        file: null,
        previewUrl: null,
        diagnostics: null,
        selectedFaceIndex: null,
        cropBox: null,
        isValidating: false,
        validationError: `File size (${(
          selectedFile.size /
          (1024 * 1024)
        ).toFixed(2)} MB) exceeds strict 10 MB limit.`,
      });
      return;
    }

    // Create ephemeral local preview URL (in-memory blob)
    const localPreview = URL.createObjectURL(selectedFile);

    onUpdateSlot({
      file: selectedFile,
      previewUrl: localPreview,
      isValidating: true,
      validationError: null,
      diagnostics: null,
      selectedFaceIndex: null,
      cropBox: null,
    });

    try {
      // Validate with backend server
      const res = await validateImageApi(selectedFile);
      if (res.is_valid && res.diagnostics) {
        const faceCount = res.diagnostics.face_count ?? 0;
        const defaultIndex = faceCount > 1 ? 0 : null;
        if (defaultIndex !== null) {
          res.diagnostics.selected_face_index = defaultIndex;
        }

        onUpdateSlot({
          isValidating: false,
          diagnostics: res.diagnostics,
          selectedFaceIndex: defaultIndex,
          cropBox: null,
          validationError: null,
        });
      } else {
        onUpdateSlot({
          isValidating: false,
          diagnostics: null,
          selectedFaceIndex: null,
          cropBox: null,
          validationError: res.error_message || 'Image failed backend security checks.',
        });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Validation request failed.';
      onUpdateSlot({
        isValidating: false,
        diagnostics: null,
        selectedFaceIndex: null,
        cropBox: null,
        validationError: msg,
      });
    }
  };

  const handleSelectFace = (index: number) => {
    if (!slot.diagnostics) return;
    const updatedDiag = {
      ...slot.diagnostics,
      selected_face_index: index,
    };
    if (slot.diagnostics.detected_faces && slot.diagnostics.detected_faces[index]) {
      const f = slot.diagnostics.detected_faces[index];
      updatedDiag.face_confidence = f.confidence;
      updatedDiag.face_bounding_box = f.box;
    }
    onUpdateSlot({
      selectedFaceIndex: index,
      diagnostics: updatedDiag,
    });
  };

  const handleApplyCrop = async (cropBox: [number, number, number, number]) => {
    if (!slot.file) return;
    onUpdateSlot({ isValidating: true, validationError: null });
    try {
      const res = await validateImageApi(slot.file, cropBox);
      if (res.is_valid && res.diagnostics) {
        const faceCount = res.diagnostics.face_count ?? 0;
        const defaultIndex = faceCount > 1 ? 0 : null;
        if (defaultIndex !== null) {
          res.diagnostics.selected_face_index = defaultIndex;
        }

        onUpdateSlot({
          isValidating: false,
          diagnostics: res.diagnostics,
          selectedFaceIndex: defaultIndex,
          cropBox,
          validationError: null,
        });
      } else {
        onUpdateSlot({
          isValidating: false,
          validationError: res.error_message || 'Cropped region validation failed.',
        });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Crop re-validation failed.';
      onUpdateSlot({ isValidating: false, validationError: msg });
    }
  };

  const handleResetCrop = async () => {
    if (!slot.file) return;
    onUpdateSlot({ isValidating: true, validationError: null });
    try {
      const res = await validateImageApi(slot.file, null);
      if (res.is_valid && res.diagnostics) {
        const faceCount = res.diagnostics.face_count ?? 0;
        const defaultIndex = faceCount > 1 ? 0 : null;
        if (defaultIndex !== null) {
          res.diagnostics.selected_face_index = defaultIndex;
        }

        onUpdateSlot({
          isValidating: false,
          diagnostics: res.diagnostics,
          selectedFaceIndex: defaultIndex,
          cropBox: null,
          validationError: null,
        });
      } else {
        onUpdateSlot({
          isValidating: false,
          validationError: res.error_message || 'Full image validation failed.',
        });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Image re-validation failed.';
      onUpdateSlot({ isValidating: false, validationError: msg });
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (disabled) return;
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled) return;
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    if (disabled) return;
    setIsDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    if (disabled) return;
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleTriggerPicker = () => {
    if (disabled) return;
    fileInputRef.current?.click();
  };

  const faceCount = slot.diagnostics?.face_count ?? 0;

  return (
    <div className="card upload-panel">
      <div className="card-header">
        <div className="card-title">
          <FileCheck2 size={16} color="var(--crimson-primary)" />
          <span>{slot.label}</span>
        </div>
        <span className="mono-badge" style={{ backgroundColor: 'var(--bg-input)', color: 'var(--text-muted)' }}>
          {slot.file ? 'FILE LOADED' : 'AWAITING INPUT'}
        </span>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          style={{ display: 'none' }}
          onChange={handleFileChange}
          disabled={disabled}
          data-testid={`file-input-${slot.id}`}
          aria-label={`Select image file for ${slot.label}`}
        />

        {/* Empty / Dropzone State */}
        {!slot.previewUrl && (
          <div
            className={`upload-dropzone ${isDragActive ? 'drag-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={handleTriggerPicker}
            role="button"
            tabIndex={disabled ? -1 : 0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') handleTriggerPicker();
            }}
            aria-label={`Upload image for ${slot.label}`}
            style={{
              opacity: disabled ? 0.6 : 1,
              cursor: disabled ? 'not-allowed' : 'pointer',
            }}
          >
            <div className="dropzone-icon-ring">
              <UploadCloud size={24} />
            </div>
            <div className="dropzone-label">Click or Drag &amp; Drop Image</div>
            <div className="dropzone-subtext">
              JPEG, PNG, or WebP up to 10 MB. Verified via magic bytes, YuNet localization &amp; SFace.
            </div>
          </div>
        )}

        {/* Loaded Image State */}
        {slot.previewUrl && (
          <div>
            <ImagePreview
              previewUrl={slot.previewUrl}
              diagnostics={slot.diagnostics}
              onReplace={handleTriggerPicker}
              onRemove={onClearSlot}
              slotLabel={slot.label}
              disabled={disabled}
              selectedFaceIndex={slot.selectedFaceIndex}
              onSelectFace={handleSelectFace}
              onOpenCrop={() => setIsCropModalOpen(true)}
              onResetCrop={slot.cropBox ? handleResetCrop : undefined}
            />

            {/* Loading Validation State */}
            {slot.isValidating && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px',
                  marginTop: '12px',
                  backgroundColor: 'var(--bg-surface)',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                  color: 'var(--text-muted)',
                }}
              >
                <Loader2 size={16} className="spin-icon" color="var(--crimson-primary)" />
                <span>Running YuNet face localization &amp; biometric telemetry...</span>
              </div>
            )}

            {/* Multi-Face Selection Bar */}
            {slot.diagnostics && slot.diagnostics.detected_faces && slot.diagnostics.detected_faces.length > 1 && (
              <FaceSelectionBar
                faces={slot.diagnostics.detected_faces}
                selectedFaceIndex={slot.selectedFaceIndex}
                onSelectFace={handleSelectFace}
                disabled={disabled}
              />
            )}

            {/* Zero Face Recovery Banner */}
            {slot.diagnostics && faceCount === 0 && !slot.isValidating && (
              <div
                className="alert-banner alert-crimson"
                style={{
                  marginTop: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                  flexWrap: 'wrap',
                }}
                role="alert"
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <AlertTriangle size={16} style={{ flexShrink: 0 }} />
                  <span style={{ fontSize: '12px' }}>
                    <strong>No face detected.</strong> Use Manual Crop to frame the face region.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setIsCropModalOpen(true)}
                  disabled={disabled}
                  className="btn btn-primary btn-sm"
                  style={{
                    backgroundColor: 'var(--crimson-primary)',
                    borderColor: 'var(--crimson-border)',
                  }}
                >
                  <Crop size={13} />
                  <span>Manual Face Crop</span>
                </button>
              </div>
            )}

            {/* Technical Diagnostics */}
            {slot.diagnostics && (
              <QualityDiagnostics diagnostics={slot.diagnostics} />
            )}

            {/* Manual Crop Modal */}
            {isCropModalOpen && slot.diagnostics && (
              <ManualCropModal
                isOpen={isCropModalOpen}
                onClose={() => setIsCropModalOpen(false)}
                imageUrl={slot.previewUrl}
                imageWidth={slot.diagnostics.width}
                imageHeight={slot.diagnostics.height}
                initialCropBox={slot.cropBox}
                onApplyCrop={handleApplyCrop}
              />
            )}
          </div>
        )}

        {/* Error Notification */}
        {slot.validationError && (
          <div
            className="alert-banner alert-crimson"
            style={{ marginTop: '16px' }}
            role="alert"
          >
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <div>
              <strong>Validation Error:</strong> {slot.validationError}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
