import React from 'react';
import {
  ShieldAlert,
  Cpu,
  Layers,
  FileCode,
  Download,
  Sparkles,
} from 'lucide-react';
import type { ComparisonResponse } from '../../types';

interface ResultPanelProps {
  result: ComparisonResponse;
  onClear: () => void;
}

export const ResultPanel: React.FC<ResultPanelProps> = ({ result }) => {
  const handleExportJSON = () => {
    const jsonStr = JSON.stringify(result, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `facecore-evaluation-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card results-card" style={{ marginTop: '24px' }}>
      <div className="card-header">
        <div className="card-title">
          <Layers size={18} color="var(--crimson-primary)" />
          <span>Evaluation Outcome & Modular Diagnostics</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleExportJSON}
            className="btn btn-secondary btn-sm"
            title="Download complete technical report as JSON"
          >
            <Download size={13} />
            <span>Export Telemetry (JSON)</span>
          </button>
        </div>
      </div>

      <div className="card-body">
        {/* Prominent Scientific Integrity Banner */}
        <div
          className="alert-banner alert-amber"
          style={{ marginBottom: '20px' }}
          role="status"
        >
          <ShieldAlert size={22} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '4px' }}>
              INFERENCE ENGINE NOT CONFIGURED (STEP 01 BASELINE)
            </div>
            <p style={{ fontSize: '13px', lineHeight: '1.5' }}>
              {result.interpretation_notice}
            </p>
          </div>
        </div>

        {/* Telemetry Stat Cards */}
        <div className="results-hero-grid">
          <div className="stat-metric-box">
            <span className="stat-label">Active Inference Engine</span>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginTop: '4px',
              }}
            >
              <Cpu size={18} color="var(--amber-primary)" />
              <span className="stat-val" style={{ fontSize: '16px' }}>
                {result.engine.name}
              </span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Version {result.engine.version} // Status: {result.engine.status}
            </span>
          </div>

          <div className="stat-metric-box">
            <span className="stat-label">Biometric Similarity Score</span>
            <div
              style={{
                display: 'flex',
                alignItems: 'baseline',
                gap: '8px',
                marginTop: '4px',
              }}
            >
              <span
                className="stat-val"
                style={{
                  fontSize: '22px',
                  color: 'var(--text-dim)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                &mdash;&mdash;
              </span>
              <span className="badge-tag amber" style={{ fontSize: '10px' }}>
                WITHHELD (UNCONFIGURED)
              </span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              No mock score is simulated. Awaiting Step 02 neural backbone.
            </span>
          </div>
        </div>

        {/* Pair Comparison Matrix */}
        <div
          style={{
            backgroundColor: 'var(--bg-input)',
            borderRadius: '8px',
            border: '1px solid var(--border-subtle)',
            padding: '16px',
            marginBottom: '20px',
          }}
        >
          <h4
            style={{
              fontSize: '13px',
              color: 'var(--text-bright)',
              marginBottom: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <FileCode size={15} color="var(--crimson-primary)" />
            <span>Image Pair Differential Analysis</span>
          </h4>

          <table className="diagnostics-matrix">
            <thead>
              <tr>
                <th>Comparison Parameter</th>
                <th>Image A (Probe)</th>
                <th>Image B (Reference)</th>
                <th>Differential Assessment</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Resolution</td>
                <td className="mono-text">
                  {result.image_a_diagnostics.width} &times;{' '}
                  {result.image_a_diagnostics.height} px
                </td>
                <td className="mono-text">
                  {result.image_b_diagnostics.width} &times;{' '}
                  {result.image_b_diagnostics.height} px
                </td>
                <td>
                  {result.image_a_diagnostics.width ===
                    result.image_b_diagnostics.width &&
                  result.image_a_diagnostics.height ===
                    result.image_b_diagnostics.height ? (
                    <span className="badge-tag emerald">Identical</span>
                  ) : (
                    <span className="badge-tag slate">Scale Variance</span>
                  )}
                </td>
              </tr>

              <tr>
                <td>Estimated Sharpness</td>
                <td className="mono-text">
                  {result.image_a_diagnostics.estimated_sharpness}
                </td>
                <td className="mono-text">
                  {result.image_b_diagnostics.estimated_sharpness}
                </td>
                <td>
                  <span className="mono-text" style={{ color: 'var(--text-muted)' }}>
                    &Delta;{' '}
                    {Math.abs(
                      result.image_a_diagnostics.estimated_sharpness -
                        result.image_b_diagnostics.estimated_sharpness
                    ).toFixed(1)}
                  </span>
                </td>
              </tr>

              <tr>
                <td>Contrast Dynamic Range</td>
                <td className="mono-text">
                  &sigma; = {result.image_a_diagnostics.contrast_std}
                </td>
                <td className="mono-text">
                  &sigma; = {result.image_b_diagnostics.contrast_std}
                </td>
                <td>
                  <span className="mono-text" style={{ color: 'var(--text-muted)' }}>
                    &Delta;{' '}
                    {Math.abs(
                      result.image_a_diagnostics.contrast_std -
                        result.image_b_diagnostics.contrast_std
                    ).toFixed(1)}
                  </span>
                </td>
              </tr>

              <tr>
                <td>Cryptographic SHA-256</td>
                <td className="mono-text" style={{ color: '#38bdf8' }}>
                  {result.image_a_diagnostics.sha256_hash}
                </td>
                <td className="mono-text" style={{ color: '#38bdf8' }}>
                  {result.image_b_diagnostics.sha256_hash}
                </td>
                <td>
                  {result.image_a_diagnostics.sha256_hash ===
                  result.image_b_diagnostics.sha256_hash ? (
                    <span className="badge-tag crimson">Identical Bitstream</span>
                  ) : (
                    <span className="badge-tag emerald">Distinct Bitstreams</span>
                  )}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Scientific Cautious Interpretation Notice */}
        <div
          style={{
            padding: '16px',
            backgroundColor: 'var(--bg-surface)',
            borderRadius: '8px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: 'var(--text-bright)',
              fontSize: '13px',
              fontWeight: 600,
              marginBottom: '6px',
            }}
          >
            <Sparkles size={14} color="var(--crimson-primary)" />
            <span>Biometric Principles & Planned Model Architecture (Phase 2 Roadmap)</span>
          </div>
          <p
            style={{
              fontSize: '12px',
              color: 'var(--text-muted)',
              lineHeight: '1.6',
              marginBottom: '10px',
            }}
          >
            Facial recognition models compute vector representations (embeddings)
            in a high-dimensional hypersphere (e.g., 512 dimensions for ArcFace).
            Cosine similarity reflects distance in that latent space. A score is a
            continuous probabilistic proximity measure—never an absolute verdict of
            identity. Threshold calibration requires balancing False Accept Rate
            (FAR) and False Reject Rate (FRR) under controlled biometric test protocols.
          </p>
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '8px',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
              PLANNED BACKBONES:
            </span>
            {result.engine.supported_models.map((m, idx) => (
              <span key={idx} className="badge-tag slate">
                {m}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
