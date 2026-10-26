import React from 'react';
import { ScanFace } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Data Evaluated',
  description = 'Upload Image A and Image B to execute technical validation and prepare for model evaluation.',
  actionText,
  onAction,
  icon,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 24px',
        textAlign: 'center',
        border: '1px dashed var(--border-medium)',
        borderRadius: '10px',
        backgroundColor: 'rgba(14, 18, 26, 0.4)',
      }}
    >
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: 'var(--bg-input)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-muted)',
          marginBottom: '16px',
        }}
      >
        {icon || <ScanFace size={28} />}
      </div>
      <h3 style={{ fontSize: '15px', color: 'var(--text-bright)', marginBottom: '8px' }}>
        {title}
      </h3>
      <p
        style={{
          fontSize: '13px',
          color: 'var(--text-muted)',
          maxWidth: '440px',
          lineHeight: '1.5',
          marginBottom: actionText ? '20px' : '0',
        }}
      >
        {description}
      </p>
      {actionText && onAction && (
        <button onClick={onAction} className="btn btn-secondary btn-sm">
          {actionText}
        </button>
      )}
    </div>
  );
};
