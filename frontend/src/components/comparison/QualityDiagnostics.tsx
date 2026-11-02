import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  Info,
  Maximize2,
  Sun,
  Activity,
  Hash,
  UserCheck,
} from 'lucide-react';
import type { ImageQualityDiagnostics } from '../../types';

interface QualityDiagnosticsProps {
  diagnostics: ImageQualityDiagnostics;
  title?: string;
}

export const QualityDiagnostics: React.FC<QualityDiagnosticsProps> = ({
  diagnostics,
  title = 'Image Quality & Cryptographic Diagnostics',
}) => {
  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-input)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '8px',
        overflow: 'hidden',
        marginTop: '16px',
      }}
    >
      <div
        style={{
          padding: '10px 14px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'var(--bg-surface)',
        }}
      >
        <span
          style={{
            fontSize: '12px',
            fontWeight: 600,
            color: 'var(--text-bright)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Info size={14} color="var(--crimson-primary)" />
          {title}
        </span>
        <span
          className={`badge-tag ${
            (diagnostics.face_count ?? 0) === 0
              ? 'crimson'
              : diagnostics.passes_quality_check
              ? 'emerald'
              : 'amber'
          }`}
          style={(diagnostics.face_count ?? 0) === 0 ? { backgroundColor: 'rgba(239, 68, 68, 0.15)', color: 'var(--crimson-primary)', borderColor: 'var(--crimson-border)' } : undefined}
        >
          {(diagnostics.face_count ?? 0) === 0 ? (
            <>
              <AlertTriangle size={11} /> No Face Localized
            </>
          ) : diagnostics.passes_quality_check ? (
            <>
              <CheckCircle2 size={11} /> Pass
            </>
          ) : (
            <>
              <AlertTriangle size={11} /> Advisory
            </>
          )}
        </span>
      </div>

      <table className="diagnostics-matrix">
        <thead>
          <tr>
            <th>Telemetry Field</th>
            <th>Measured Value</th>
            <th>Baseline Criterion</th>
          </tr>
        </thead>
        <tbody>
          {diagnostics.face_count !== undefined && (
            <tr>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <UserCheck size={12} color={(diagnostics.face_count ?? 0) > 0 ? "var(--emerald-primary)" : "var(--crimson-primary)"} />
                  <span>Face Localization</span>
                </div>
              </td>
              <td>
                <span
                  className="mono-text"
                  style={{
                    color:
                      diagnostics.face_count === 1
                        ? 'var(--emerald-primary)'
                        : diagnostics.face_count > 1
                        ? 'var(--amber-primary)'
                        : 'var(--crimson-primary)',
                    fontWeight: 600,
                  }}
                >
                  {diagnostics.face_count === 1
                    ? `1 Face (${diagnostics.face_confidence ? (diagnostics.face_confidence * 100).toFixed(1) : '100'}% conf)`
                    : diagnostics.face_count > 1
                    ? `${diagnostics.face_count} Faces Detected ${
                        diagnostics.selected_face_index !== null && diagnostics.selected_face_index !== undefined
                          ? `(Face #${diagnostics.selected_face_index + 1} Active)`
                          : '(Selection Required)'
                      }`
                    : '0 Faces Detected'}
                </span>
              </td>
              <td style={{ color: 'var(--text-dim)' }}>
                {diagnostics.face_count > 1 ? 'Select 1 Face for Comparison' : 'Exactly 1 Face Required'}
              </td>
            </tr>
          )}

          {diagnostics.face_bounding_box && (
            <tr>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <Maximize2 size={12} color="var(--text-muted)" />
                  <span>Face Bounding Box</span>
                </div>
              </td>
              <td>
                <span className="mono-text" style={{ color: 'var(--text-bright)' }}>
                  [{diagnostics.face_bounding_box.join(', ')}] px
                </span>
              </td>
              <td style={{ color: 'var(--text-dim)' }}>&ge; 16 &times; 16 px</td>
            </tr>
          )}

          {diagnostics.crop_bounding_box && (
            <tr>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <Maximize2 size={12} color="var(--crimson-primary)" />
                  <span>Manual Crop Framing</span>
                </div>
              </td>
              <td>
                <span className="mono-text" style={{ color: 'var(--crimson-primary)' }}>
                  [{diagnostics.crop_bounding_box.join(', ')}] px
                </span>
              </td>
              <td style={{ color: 'var(--text-dim)' }}>User Region Constraint</td>
            </tr>
          )}

          <tr>
            <td>Container / Color Space</td>
            <td>
              <span className="mono-text" style={{ color: 'var(--text-bright)' }}>
                {diagnostics.format} / {diagnostics.color_mode}
              </span>
            </td>
            <td style={{ color: 'var(--text-dim)' }}>JPEG / PNG / WebP</td>
          </tr>

          <tr>
            <td>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <Maximize2 size={12} color="var(--text-muted)" />
                <span>Pixel Resolution</span>
              </div>
            </td>
            <td>
              <span className="mono-text" style={{ color: 'var(--text-bright)' }}>
                {diagnostics.width} &times; {diagnostics.height} px ({diagnostics.aspect_ratio})
              </span>
            </td>
            <td style={{ color: 'var(--text-dim)' }}>&ge; 32 &times; 32 px</td>
          </tr>

          <tr>
            <td>Fidelity Tier</td>
            <td>
              <span style={{ color: 'var(--text-bright)' }}>
                {diagnostics.resolution_category}
              </span>
            </td>
            <td style={{ color: 'var(--text-dim)' }}>Standard / High Tier</td>
          </tr>

          <tr>
            <td>Payload Size</td>
            <td className="mono-text" style={{ color: 'var(--text-bright)' }}>
              {formatBytes(diagnostics.file_size_bytes)}
            </td>
            <td style={{ color: 'var(--text-dim)' }}>&le; 10 MB</td>
          </tr>

          <tr>
            <td>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <Hash size={12} color="var(--text-muted)" />
                <span>SHA-256 Fingerprint</span>
              </div>
            </td>
            <td className="mono-text" style={{ color: '#38bdf8' }}>
              {diagnostics.sha256_hash}...
            </td>
            <td style={{ color: 'var(--text-dim)' }}>Cryptographic Provenance</td>
          </tr>

          <tr>
            <td>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <Activity size={12} color="var(--text-muted)" />
                <span>Sharpness (Laplacian Var)</span>
              </div>
            </td>
            <td className="mono-text" style={{ color: 'var(--text-bright)' }}>
              {diagnostics.estimated_sharpness > 0
                ? diagnostics.estimated_sharpness
                : 'N/A (<5px)'}
            </td>
            <td style={{ color: 'var(--text-dim)' }}>Baseline &gt; 25.0</td>
          </tr>

          <tr>
            <td>
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <Sun size={12} color="var(--text-muted)" />
                <span>Luma Brightness & Contrast</span>
              </div>
            </td>
            <td className="mono-text" style={{ color: 'var(--text-bright)' }}>
              Mean: {diagnostics.brightness_mean} / Std: {diagnostics.contrast_std}
            </td>
            <td style={{ color: 'var(--text-dim)' }}>Mean 40-220, Std &gt; 18</td>
          </tr>
        </tbody>
      </table>

      {/* Advisories if present */}
      {diagnostics.warnings && diagnostics.warnings.length > 0 && (
        <div
          style={{
            padding: '10px 14px',
            backgroundColor: 'rgba(245, 158, 11, 0.08)',
            borderTop: '1px solid var(--amber-border)',
          }}
        >
          <div
            style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--amber-primary)',
              marginBottom: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <AlertTriangle size={12} />
            <span>QUALITY ADVISORIES:</span>
          </div>
          <ul
            style={{
              paddingLeft: '18px',
              fontSize: '11px',
              color: '#fde68a',
              lineHeight: '1.4',
            }}
          >
            {diagnostics.warnings.map((warn, idx) => (
              <li key={idx}>{warn}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
