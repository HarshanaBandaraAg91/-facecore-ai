import React, { useRef, useState } from 'react';
import {
  UploadCloud,
  FileCheck2,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import type { UploadedImageSlot } from '../../types';
import { ImagePreview } from './ImagePreview';
import { QualityDiagnostics } from './QualityDiagnostics';
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

  const processFile = async (selectedFile: File) => {
    // Client-side quick sanity check
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(selectedFile.type)) {
      onUpdateSlot({
        file: null,
        previewUrl: null,
        diagnostics: null,
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
    });

    try {
      // Validate with backend server
      const res = await validateImageApi(selectedFile);
      if (res.is_valid && res.diagnostics) {
        onUpdateSlot({
          isValidating: false,
          diagnostics: res.diagnostics,
          validationError: null,
        });
      } else {
        onUpdateSlot({
          isValidating: false,
          diagnostics: null,
          validationError: res.error_message || 'Image failed backend security checks.',
        });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Validation request failed.';
      onUpdateSlot({
        isValidating: false,
        diagnostics: null,
        validationError: msg,
      });
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
            <div className="dropzone-label">Click or Drag & Drop Image</div>
            <div className="dropzone-subtext">
              JPEG, PNG, or WebP up to 10 MB. Verified via magic bytes & safe decoding.
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
                <span>Validating container signature & pixel integrity...</span>
              </div>
            )}

            {/* Technical Diagnostics */}
            {slot.diagnostics && (
              <QualityDiagnostics diagnostics={slot.diagnostics} />
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
