import React from 'react';
import {
  FlaskConical,
  Database,
  GitBranch,
  Target,
  Sparkles,
} from 'lucide-react';

export const TestLabView: React.FC = () => {
  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', color: 'var(--text-bright)', marginBottom: '6px' }}>
          Test Lab & Batch Evaluation Suite
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Systematic offline evaluation framework for measuring biometric verification accuracy,
          error distributions, and cross-demographic robustness.
        </p>
      </div>

      {/* Status banner */}
      <div className="alert-banner alert-blue" style={{ marginBottom: '24px' }}>
        <Sparkles size={20} style={{ flexShrink: 0 }} />
        <div>
          <strong>Phase 1 Architecture Staged:</strong> Batch test harness is scheduled for Phase 3.
          This view outlines the formalized testing protocol, genuine/impostor distribution curves,
          and authorized evaluation datasets. No test datasets have been downloaded in this phase.
        </div>
      </div>

      {/* Grid of Planned Capabilities */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '20px',
          marginBottom: '24px',
        }}
      >
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Database size={16} color="var(--crimson-primary)" />
              <span>Authorized Test Staging</span>
            </div>
            <span className="badge-tag slate">Phase 3 Spec</span>
          </div>
          <div className="card-body">
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '14px' }}>
              Standardized pairing protocols designed to prevent dataset contamination.
              All test sets will be held in isolated local stores under strict data-governance
              compliance with zero cloud syncing.
            </p>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '6px 8px',
                  backgroundColor: 'var(--bg-input)',
                  borderRadius: '4px',
                }}
              >
                <span style={{ color: 'var(--text-bright)' }}>LFW Protocol</span>
                <span style={{ color: 'var(--text-dim)' }}>6,000 standard pairs (10-fold)</span>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '6px 8px',
                  backgroundColor: 'var(--bg-input)',
                  borderRadius: '4px',
                }}
              >
                <span style={{ color: 'var(--text-bright)' }}>CFP-FP (Pose)</span>
                <span style={{ color: 'var(--text-dim)' }}>7,000 frontal-profile pairs</span>
              </div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '6px 8px',
                  backgroundColor: 'var(--bg-input)',
                  borderRadius: '4px',
                }}
              >
                <span style={{ color: 'var(--text-bright)' }}>AgeDB-30 (Aging)</span>
                <span style={{ color: 'var(--text-dim)' }}>6,000 age-gap pairs</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Target size={16} color="var(--crimson-primary)" />
              <span>Statistical Accuracy Metrics</span>
            </div>
            <span className="badge-tag amber">Upcoming</span>
          </div>
          <div className="card-body">
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '14px' }}>
              Continuous decision threshold sweeping to establish ROC and DET curves.
              Scores will be evaluated across multiple operational operating points:
            </p>
            <ul
              style={{
                paddingLeft: '18px',
                fontSize: '12px',
                color: 'var(--text-main)',
                lineHeight: '1.8',
              }}
            >
              <li>
                <strong>FAR @ 1e-3 & 1e-4:</strong> False Acceptance Rate operating points
              </li>
              <li>
                <strong>Equal Error Rate (EER):</strong> Equilibrium threshold where FAR = FRR
              </li>
              <li>
                <strong>AUC-ROC:</strong> Overall discrimination capability across all thresholds
              </li>
              <li>
                <strong>Score Calibration:</strong> Platt scaling and temperature scaling
              </li>
            </ul>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <GitBranch size={16} color="var(--crimson-primary)" />
              <span>Repeatable Experiment Runner</span>
            </div>
            <span className="badge-tag emerald">Local Harness</span>
          </div>
          <div className="card-body">
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '14px' }}>
              Configurable experiment runner executing reproducible test runs. Every
              experiment will record git commit hash, model weights checksum, input
              preprocessing pipeline parameters, and deterministic seed states.
            </p>
            <div
              style={{
                padding: '10px',
                backgroundColor: 'var(--bg-input)',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                color: 'var(--text-muted)',
              }}
            >
              <code>python -m app.eval.run_batch --protocol lfw --seed 42</code>
            </div>
          </div>
        </div>
      </div>

      {/* Current State Info */}
      <div
        className="card"
        style={{
          borderLeft: '4px solid var(--amber-primary)',
        }}
      >
        <div className="card-body" style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <FlaskConical size={32} color="var(--amber-primary)" style={{ flexShrink: 0 }} />
          <div>
            <h4 style={{ fontSize: '14px', color: 'var(--text-bright)', marginBottom: '4px' }}>
              Execution Suspended for Phase 1
            </h4>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Per Step 01 constraints, model training, dataset acquisition, and benchmark execution
              are deferred. Once a verified embedding backbone is mounted in Step 02, automated batch
              evaluation will be unlocked.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
