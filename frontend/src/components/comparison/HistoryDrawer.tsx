import React from 'react';
import {
  X,
  History,
  Trash2,
  ShieldCheck,
  Hash,
  Clock,
  Layers,
} from 'lucide-react';
import type { ComparisonHistoryEntry } from '../../types';

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  history: ComparisonHistoryEntry[];
  onClearHistory: () => void;
}

export const HistoryDrawer: React.FC<HistoryDrawerProps> = ({
  isOpen,
  onClose,
  history,
  onClearHistory,
}) => {
  if (!isOpen) return null;

  return (
    <div
      className="drawer-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Evaluation Session History"
    >
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <History size={18} color="var(--crimson-primary)" />
            <h3 style={{ fontSize: '14px', color: 'var(--text-bright)' }}>
              Evaluation Session Log
            </h3>
          </div>
          <button
            onClick={onClose}
            className="btn btn-secondary btn-sm"
            aria-label="Close drawer"
          >
            <X size={15} />
          </button>
        </div>

        {/* Privacy declaration notice */}
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: 'var(--bg-input)',
            borderBottom: '1px solid var(--border-subtle)',
            fontSize: '11px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: 'var(--emerald-primary)',
            fontFamily: 'var(--font-mono)',
          }}
        >
          <ShieldCheck size={14} style={{ flexShrink: 0 }} />
          <span>METADATA-ONLY RETENTION (EPHEMERAL PRIVACY)</span>
        </div>

        <div className="drawer-content">
          {history.length === 0 ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '40px 16px',
                textAlign: 'center',
                color: 'var(--text-muted)',
              }}
            >
              <History size={32} style={{ opacity: 0.4, marginBottom: '12px' }} />
              <div style={{ fontSize: '13px', color: 'var(--text-bright)', marginBottom: '4px' }}>
                No Evaluations Executed Yet
              </div>
              <p style={{ fontSize: '11px', maxWidth: '240px' }}>
                When you compare two validated images, evaluation telemetry will appear here.
              </p>
            </div>
          ) : (
            history.map((entry) => (
              <div key={entry.id} className="history-card">
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    borderBottom: '1px solid var(--border-subtle)',
                    paddingBottom: '6px',
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      color: 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Clock size={11} />
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                  {entry.rawCosineScore !== undefined && entry.rawCosineScore !== null ? (
                    <span
                      className={`badge-tag ${
                        entry.isMatch ? 'emerald' : 'cyan'
                      }`}
                      style={{ fontSize: '10px' }}
                    >
                      COS: {entry.rawCosineScore >= 0 ? '+' : ''}{entry.rawCosineScore.toFixed(3)}
                    </span>
                  ) : (
                    <span className="badge-tag amber" style={{ fontSize: '10px' }}>
                      MODULAR STUB
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Probe (A):</span>
                    <span style={{ color: 'var(--text-bright)' }}>{entry.imageAName}</span>
                  </div>
                  <div
                    className="mono-text"
                    style={{
                      fontSize: '10px',
                      color: '#38bdf8',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Hash size={10} />
                    <span>SHA: {entry.hashAPrefix} ({entry.dimensionsA})</span>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Reference (B):</span>
                    <span style={{ color: 'var(--text-bright)' }}>{entry.imageBName}</span>
                  </div>
                  <div
                    className="mono-text"
                    style={{
                      fontSize: '10px',
                      color: '#38bdf8',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Hash size={10} />
                    <span>SHA: {entry.hashBPrefix} ({entry.dimensionsB})</span>
                  </div>
                </div>

                <div
                  style={{
                    fontSize: '10px',
                    color: 'var(--text-dim)',
                    fontFamily: 'var(--font-mono)',
                    borderTop: '1px solid var(--border-subtle)',
                    paddingTop: '6px',
                    marginTop: '2px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Layers size={10} />
                    <span>{entry.engineName}</span>
                  </div>
                  {entry.isMatch !== undefined && entry.isMatch !== null && (
                    <span style={{ color: entry.isMatch ? 'var(--emerald-primary)' : 'var(--cyan-primary)' }}>
                      [Exp: {entry.isMatch ? 'Match' : 'Different'}]
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {history.length > 0 && (
          <div
            style={{
              padding: '16px',
              borderTop: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
              {history.length} {history.length === 1 ? 'entry' : 'entries'} stored
            </span>
            <button
              onClick={onClearHistory}
              className="btn btn-secondary btn-sm"
              style={{ color: '#fda4af' }}
            >
              <Trash2 size={13} />
              <span>Clear Session Log</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
