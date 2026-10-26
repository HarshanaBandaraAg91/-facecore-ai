import React from 'react';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title?: string;
  message: string;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        maxWidth: '420px',
        width: '100%',
      }}
    >
      {toasts.map((toast) => {
        let alertClass = 'alert-blue';
        let Icon = Info;
        if (toast.type === 'success') {
          alertClass = 'alert-emerald';
          Icon = CheckCircle2;
        } else if (toast.type === 'error') {
          alertClass = 'alert-crimson';
          Icon = AlertCircle;
        } else if (toast.type === 'warning') {
          alertClass = 'alert-amber';
          Icon = AlertCircle;
        }

        return (
          <div
            key={toast.id}
            className={`alert-banner ${alertClass}`}
            style={{
              boxShadow: 'var(--shadow-lg)',
              animation: 'fadeInUp 0.2s ease-out',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Icon size={18} style={{ flexShrink: 0 }} />
              <div>
                {toast.title && (
                  <div style={{ fontWeight: 600, fontSize: '12px' }}>{toast.title}</div>
                )}
                <div style={{ fontSize: '12px' }}>{toast.message}</div>
              </div>
            </div>
            <button
              onClick={() => onDismiss(toast.id)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'currentColor',
                cursor: 'pointer',
                opacity: 0.7,
                padding: '4px',
              }}
              aria-label="Dismiss toast"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
};
