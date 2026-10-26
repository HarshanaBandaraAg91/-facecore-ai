import React from 'react';
import {
  BarChart3,
  ShieldAlert,
  AlertCircle,
  FileCheck2,
  Calendar,
} from 'lucide-react';

export const BenchmarksView: React.FC = () => {
  const benchmarkProtocols = [
    {
      name: 'Labeled Faces in the Wild (LFW)',
      description: 'Unconstrained facial verification across 13,233 images / 5,749 identities',
      plannedModel: 'ArcFace (ResNet-100)',
      targetAccuracy: '99.82% (Literature Reference)',
      status: 'AWAITING RUN',
    },
    {
      name: 'Celebrities in Frontal-Profile (CFP-FP)',
      description: 'Cross-pose robustness evaluation (frontal vs profile yaw variation)',
      plannedModel: 'AdaFace (IR-50)',
      targetAccuracy: '98.40% (Literature Reference)',
      status: 'AWAITING RUN',
    },
    {
      name: 'AgeDB-30',
      description: 'Age-invariant face verification across large temporal age gaps (30-year span)',
      plannedModel: 'ArcFace (ResNet-100)',
      targetAccuracy: '98.15% (Literature Reference)',
      status: 'AWAITING RUN',
    },
    {
      name: 'IJB-C 1:1 Verification',
      description: 'Challenging mixed-media video frame and surveillance image verification',
      plannedModel: 'MagFace (ResNet-50)',
      targetAccuracy: 'TAR @ FAR=1e-4: 96.2% (Target)',
      status: 'AWAITING RUN',
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', color: 'var(--text-bright)', marginBottom: '6px' }}>
          Standardized Model Benchmarks
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Transparent benchmarking registry for tracking accuracy, false-match trade-offs, and
          inference latencies across verified neural backbones.
        </p>
      </div>

      {/* Prominent disclaimer that no benchmark has run yet */}
      <div className="alert-banner alert-amber" style={{ marginBottom: '24px' }}>
        <ShieldAlert size={20} style={{ flexShrink: 0 }} />
        <div>
          <strong>NO BENCHMARKS EXECUTED YET:</strong> Per scientific integrity requirements,
          zero benchmark percentages or model accuracy scores have been simulated or fabricated.
          The evaluation suite will be initiated only after an authorized model backbone is
          mounted and test sets are partitioned in Step 02/03.
        </div>
      </div>

      {/* Benchmark Registry Table */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">
            <BarChart3 size={16} color="var(--crimson-primary)" />
            <span>Standard Evaluation Protocols</span>
          </div>
          <span className="badge-tag amber">Status: Zero Executed</span>
        </div>

        <div className="card-body" style={{ padding: 0 }}>
          <table className="diagnostics-matrix" style={{ margin: 0 }}>
            <thead>
              <tr>
                <th>Protocol / Benchmark Suite</th>
                <th>Target Evaluation Backbone</th>
                <th>Published Reference Baseline</th>
                <th>FACECORE Measured Accuracy</th>
                <th>Audit Status</th>
              </tr>
            </thead>
            <tbody>
              {benchmarkProtocols.map((b, idx) => (
                <tr key={idx}>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-bright)' }}>
                      {b.name}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      {b.description}
                    </div>
                  </td>
                  <td>
                    <span className="mono-text" style={{ color: 'var(--text-main)' }}>
                      {b.plannedModel}
                    </span>
                  </td>
                  <td>
                    <span className="mono-text" style={{ color: 'var(--text-muted)' }}>
                      {b.targetAccuracy}
                    </span>
                  </td>
                  <td>
                    <span
                      className="mono-text"
                      style={{
                        color: 'var(--amber-primary)',
                        fontWeight: 600,
                        backgroundColor: 'var(--bg-input)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        display: 'inline-block',
                      }}
                    >
                      &mdash;&mdash; (Unrun)
                    </span>
                  </td>
                  <td>
                    <span className="badge-tag amber">{b.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Methodology Card */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <FileCheck2 size={16} color="var(--crimson-primary)" />
            <span>Benchmarking Protocol & Anti-Fabrication Principles</span>
          </div>
          <span className="badge-tag emerald">Strict Compliance</span>
        </div>
        <div className="card-body">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '16px',
            }}
          >
            <div
              style={{
                backgroundColor: 'var(--bg-input)',
                padding: '14px',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: 'var(--text-bright)',
                  fontSize: '12px',
                  fontWeight: 600,
                  marginBottom: '6px',
                }}
              >
                <AlertCircle size={14} color="var(--crimson-primary)" />
                <span>Zero Score Fabrication</span>
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                All results must originate from verifiable local batch runs. Synthetic
                percentages or placeholders that could mislead operators are strictly prohibited.
              </p>
            </div>

            <div
              style={{
                backgroundColor: 'var(--bg-input)',
                padding: '14px',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: 'var(--text-bright)',
                  fontSize: '12px',
                  fontWeight: 600,
                  marginBottom: '6px',
                }}
              >
                <Calendar size={14} color="var(--emerald-primary)" />
                <span>Deterministic Seed Control</span>
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                Folds, pair selections, and tie-breaking algorithms must be fixed with
                published seeds so results can be independently audited.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
