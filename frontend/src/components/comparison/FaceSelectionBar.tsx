import React from 'react';
import { UserCheck, CheckCircle2, Layers } from 'lucide-react';
import type { DetectedFaceSummary } from '../../types';


interface FaceSelectionBarProps {
  faces: DetectedFaceSummary[];
  selectedFaceIndex: number | null | undefined;
  onSelectFace: (index: number) => void;
  disabled?: boolean;
}

export const FaceSelectionBar: React.FC<FaceSelectionBarProps> = ({
  faces,
  selectedFaceIndex,
  onSelectFace,
  disabled = false,
}) => {
  if (!faces || faces.length <= 1) return null;

  const activeIndex = selectedFaceIndex ?? 0;

  return (
    <div
      className="face-selection-bar"
      style={{
        marginTop: '12px',
        padding: '12px',
        backgroundColor: 'var(--bg-surface)',
        borderRadius: '6px',
        border: '1px solid var(--amber-border)',
        boxShadow: 'inset 0 1px 4px rgba(0, 0, 0, 0.4)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '8px',
        }}
      >
        <span
          style={{
            fontSize: '11px',
            fontWeight: 700,
            fontFamily: 'var(--font-mono)',
            color: 'var(--amber-primary)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            letterSpacing: '0.4px',
          }}
        >
          <Layers size={13} />
          MULTIPLE FACES DETECTED ({faces.length} LOCATED) &mdash; SELECT TARGET:
        </span>
        <span
          className="mono-text"
          style={{
            fontSize: '10px',
            color: 'var(--emerald-primary)',
            fontWeight: 600,
          }}
        >
          ACTIVE: FACE #{activeIndex + 1}
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${Math.min(faces.length, 4)}, 1fr)`,
          gap: '8px',
        }}
      >
        {faces.map((f) => {
          const isSelected = f.index === activeIndex;
          const [bx, by, bw, bh] = f.box;

          return (
            <button
              key={f.index}
              type="button"
              disabled={disabled}
              onClick={() => onSelectFace(f.index)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start',
                padding: '8px 10px',
                borderRadius: '5px',
                backgroundColor: isSelected
                  ? 'rgba(16, 185, 129, 0.12)'
                  : 'var(--bg-input)',
                border: isSelected
                  ? '1px solid var(--emerald-primary)'
                  : '1px solid var(--border-subtle)',
                boxShadow: isSelected
                  ? '0 0 10px rgba(16, 185, 129, 0.25)'
                  : 'none',
                cursor: disabled ? 'not-allowed' : 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  marginBottom: '3px',
                }}
              >
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    color: isSelected ? 'var(--emerald-primary)' : 'var(--text-bright)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  {isSelected ? <CheckCircle2 size={12} color="var(--emerald-primary)" /> : <UserCheck size={12} color="var(--text-dim)" />}
                  Face #{f.index + 1}
                </span>
                <span
                  className="mono-text"
                  style={{
                    fontSize: '10px',
                    color: isSelected ? 'var(--emerald-primary)' : 'var(--text-muted)',
                  }}
                >
                  {(f.confidence * 100).toFixed(1)}%
                </span>
              </div>

              <div
                className="mono-text"
                style={{
                  fontSize: '9px',
                  color: 'var(--text-dim)',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  width: '100%',
                }}
              >
                [{bx}, {by}, {bw}, {bh}]
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
