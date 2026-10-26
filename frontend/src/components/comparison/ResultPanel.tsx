import React from 'react';
import {
  ShieldAlert,
  Cpu,
  Layers,
  FileCode,
  Download,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ScanFace,
  HelpCircle,
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

  const hasScore = result.raw_cosine_similarity !== null && result.raw_cosine_similarity !== undefined;
  const rawScore = result.raw_cosine_similarity ?? result.similarity_score;
  const displayScore = result.transformed_display_score;
  const isMatch = result.is_match;
  const threshold = result.provisional_threshold ?? 0.363;

  return (
    <div className="card results-card" style={{ marginTop: '0', marginBottom: '24px' }}>
      <div className="card-header">
        <div className="card-title">
          <Layers size={18} color="var(--crimson-primary)" />
          <span>Biometric Evaluation Outcome & Real Embedding Telemetry</span>
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
        {/* Status Banner */}
        {hasScore ? (
          <div
            className={`alert-banner ${isMatch ? 'alert-emerald' : 'alert-amber'}`}
            style={{ marginBottom: '20px' }}
            role="status"
          >
            {isMatch ? (
              <CheckCircle2 size={24} style={{ flexShrink: 0, marginTop: '2px' }} />
            ) : (
              <AlertTriangle size={24} style={{ flexShrink: 0, marginTop: '2px' }} />
            )}
            <div style={{ flex: 1 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '8px',
                  marginBottom: '4px',
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '14px' }}>
                  {isMatch
                    ? 'PROVISIONAL MATCH (EXPERIMENTAL BASELINE)'
                    : 'PROVISIONAL NON-MATCH (BELOW THRESHOLD)'}
                </div>
                <span className="badge-tag amber" style={{ fontSize: '10px' }}>
                  UNCALIBRATED THRESHOLD (&tau; = {threshold})
                </span>
              </div>
              <p style={{ fontSize: '13px', lineHeight: '1.5' }}>
                {result.interpretation_notice}
              </p>
            </div>
          </div>
        ) : (
          <div
            className="alert-banner alert-amber"
            style={{ marginBottom: '20px' }}
            role="status"
          >
            <ShieldAlert size={22} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '4px' }}>
                INFERENCE NOTICE
              </div>
              <p style={{ fontSize: '13px', lineHeight: '1.5' }}>
                {result.interpretation_notice}
              </p>
            </div>
          </div>
        )}

        {/* Telemetry Stat Cards */}
        <div
          className="results-hero-grid"
          style={{ gridTemplateColumns: hasScore ? 'repeat(auto-fit, minmax(220px, 1fr))' : '1fr 1fr' }}
        >
          {/* Active Model */}
          <div className="stat-metric-box">
            <span className="stat-label">Active Neural Backbone</span>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                marginTop: '4px',
              }}
            >
              <Cpu size={18} color="var(--emerald-primary)" />
              <span className="stat-val" style={{ fontSize: '15px' }}>
                {result.engine.name}
              </span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              {result.engine.embedding_dimension || 128}-d Hyperspherical Vector ({result.engine.inference_device || 'CPU'})
            </span>
          </div>

          {/* Raw Cosine Similarity */}
          {hasScore && (
            <div className="stat-metric-box">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span className="stat-label">Raw Cosine Similarity</span>
                <span
                  title="Raw dot product between unit normalized 128-d feature embeddings. Range: -1.0 to +1.0."
                  style={{ cursor: 'help', color: 'var(--text-dim)' }}
                >
                  <HelpCircle size={13} />
                </span>
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: '8px',
                  marginTop: '4px',
                }}
              >
                <span
                  className="stat-val mono-text"
                  style={{
                    fontSize: '24px',
                    color: rawScore! >= threshold ? 'var(--emerald-primary)' : 'var(--amber-primary)',
                  }}
                >
                  {rawScore! >= 0 ? `+${rawScore!.toFixed(4)}` : rawScore!.toFixed(4)}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                  [-1.0 to +1.0]
                </span>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Vector distance: &theta; = {(Math.acos(Math.max(-1, Math.min(1, rawScore!))) * (180 / Math.PI)).toFixed(1)}&deg;
              </span>
            </div>
          )}

          {/* Transformed Display Index */}
          {hasScore && displayScore !== null && displayScore !== undefined && (
            <div className="stat-metric-box">
              <span className="stat-label">Normalized Display Index</span>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: '8px',
                  marginTop: '4px',
                }}
              >
                <span
                  className="stat-val mono-text"
                  style={{ fontSize: '24px', color: 'var(--text-bright)' }}
                >
                  {displayScore.toFixed(1)}
                  <span style={{ fontSize: '14px', color: 'var(--text-dim)' }}>/100</span>
                </span>
                <span className="badge-tag slate" style={{ fontSize: '10px' }}>
                  Linear ((cos+1)/2)
                </span>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Scaled visual metric (NOT a match probability)
              </span>
            </div>
          )}

          {/* Inference Latency */}
          {result.inference_latency_ms !== null && result.inference_latency_ms !== undefined && (
            <div className="stat-metric-box">
              <span className="stat-label">Inference Execution</span>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginTop: '4px',
                }}
              >
                <Clock size={18} color="#38bdf8" />
                <span className="stat-val mono-text" style={{ fontSize: '20px' }}>
                  {result.inference_latency_ms.toFixed(1)} ms
                </span>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Local multi-threaded CPU pipeline
              </span>
            </div>
          )}
        </div>

        {/* Pair Comparison & Detection Matrix */}
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
            <span>Image Pair Biometric & Detection Differential</span>
          </h4>

          <table className="diagnostics-matrix">
            <thead>
              <tr>
                <th>Telemetry Parameter</th>
                <th>Image A (Probe)</th>
                <th>Image B (Reference)</th>
                <th>Differential Assessment</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Face Detection</td>
                <td>
                  <span className="badge-tag emerald">
                    <ScanFace size={11} />
                    {result.image_a_diagnostics.face_count || 1} Face (
                    {result.image_a_diagnostics.face_confidence
                      ? `${(result.image_a_diagnostics.face_confidence * 100).toFixed(1)}%`
                      : 'Detected'}
                    )
                  </span>
                </td>
                <td>
                  <span className="badge-tag emerald">
                    <ScanFace size={11} />
                    {result.image_b_diagnostics.face_count || 1} Face (
                    {result.image_b_diagnostics.face_confidence
                      ? `${(result.image_b_diagnostics.face_confidence * 100).toFixed(1)}%`
                      : 'Detected'}
                    )
                  </span>
                </td>
                <td>
                  <span className="badge-tag emerald">Single Face Verified</span>
                </td>
              </tr>

              <tr>
                <td>Bounding Box [x, y, w, h]</td>
                <td className="mono-text">
                  {result.image_a_diagnostics.face_bounding_box
                    ? `[${result.image_a_diagnostics.face_bounding_box.join(', ')}]`
                    : 'N/A'}
                </td>
                <td className="mono-text">
                  {result.image_b_diagnostics.face_bounding_box
                    ? `[${result.image_b_diagnostics.face_bounding_box.join(', ')}]`
                    : 'N/A'}
                </td>
                <td style={{ color: 'var(--text-dim)' }}>YuNet 5-point alignment</td>
              </tr>

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
                    <span className="badge-tag emerald">Identical Dimension</span>
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

        {/* Scientific Cautious Interpretation & Ethical Guardrails */}
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
            <span>Biometric Score Interpretation & Calibration Principles</span>
          </div>
          <p
            style={{
              fontSize: '12px',
              color: 'var(--text-muted)',
              lineHeight: '1.6',
              marginBottom: '10px',
            }}
          >
            <strong>Cosine Similarity Is Not a Match Probability:</strong> The raw score is the
            dot product of two 128-dimensional unit vectors on a hypersphere. A high score (e.g. 0.75 or 85/100)
            does <em>not</em> mean "85% confidence" or "85% certainty" that both photos show the same individual.
            Image quality heuristics (sharpness, contrast, brightness) provide diagnostic context for landmark
            localization, but must never be used as a substitute for model statistical calibration.
          </p>
          <div
            style={{
              fontSize: '11px',
              color: 'var(--text-dim)',
              fontFamily: 'var(--font-mono)',
              lineHeight: '1.5',
            }}
          >
            WEIGHTS LICENSE: {result.engine.weights_license || 'Apache-2.0'} &bull; PROVISIONAL THRESHOLD: &tau; = {threshold} &bull; DEVICE: {result.engine.inference_device || 'CPU'}
          </div>
        </div>
      </div>
    </div>
  );
};
