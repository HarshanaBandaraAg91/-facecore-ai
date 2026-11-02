import React, { useState } from 'react';
import {
  ShieldCheck,
  Palette,
  Server,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Cpu,
  Layers,
} from 'lucide-react';
import type { Theme, HealthResponse } from '../../types';
import { API_BASE_URL, fetchHealth } from '../../services/api';

interface SettingsViewProps {
  currentTheme: Theme;
  onSelectTheme: (theme: Theme) => void;
  health: HealthResponse | null;
  onRefreshHealth: () => void;
  onShowToast: (msg: {
    type: 'success' | 'error' | 'info' | 'warning';
    message: string;
    title?: string;
  }) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  currentTheme,
  onSelectTheme,
  health,
  onRefreshHealth,
  onShowToast,
}) => {
  const [testingEndpoint, setTestingEndpoint] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleTestConnection = async () => {
    setTestingEndpoint(true);
    setTestResult(null);
    try {
      const h = await fetchHealth();
      setTestResult(`Success: Connected to ${h.app} (${h.version})`);
      onRefreshHealth();
      onShowToast({
        type: 'success',
        title: 'Backend Reached',
        message: `FastAPI server responsive on ${API_BASE_URL}`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reach backend';
      setTestResult(`Connection Failed: ${msg}`);
      onShowToast({
        type: 'error',
        title: 'Connection Error',
        message: msg,
      });
    } finally {
      setTestingEndpoint(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 style={{ fontSize: '20px', color: 'var(--text-bright)', marginBottom: '6px' }}>
          Platform Settings & Privacy Architecture
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Configure theme aesthetics, inspect backend connectivity, and review local-first
          privacy policies.
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: '24px',
          marginBottom: '24px',
        }}
      >
        {/* Theme Settings */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Palette size={16} color="var(--crimson-primary)" />
              <span>Interface Theme</span>
            </div>
            <span className="badge-tag slate">Visual Profile</span>
          </div>
          <div className="card-body">
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Select a cyber-intelligence aesthetic suited to your tactical environment:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                {
                  id: 'cyber-dark' as Theme,
                  name: 'Cyber Dark (Obsidian & Crimson)',
                  desc: 'Deep black background with tactical crimson glow (Recommended)',
                },
                {
                  id: 'tactical-charcoal' as Theme,
                  name: 'Tactical Charcoal',
                  desc: 'Softened dark charcoal contrast with balanced ambient grids',
                },
                {
                  id: 'slate-minimal' as Theme,
                  name: 'Slate Minimal',
                  desc: 'High-contrast midnight slate with restrained boundaries',
                },
              ].map((t) => (
                <label
                  key={t.id}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '12px',
                    borderRadius: '6px',
                    backgroundColor:
                      currentTheme === t.id ? 'var(--bg-card-hover)' : 'var(--bg-input)',
                    border: `1px solid ${
                      currentTheme === t.id
                        ? 'var(--crimson-border)'
                        : 'var(--border-subtle)'
                    }`,
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="radio"
                    name="theme"
                    value={t.id}
                    checked={currentTheme === t.id}
                    onChange={() => onSelectTheme(t.id)}
                    style={{ marginTop: '3px', accentColor: 'var(--crimson-primary)' }}
                  />
                  <div>
                    <div
                      style={{
                        fontSize: '13px',
                        fontWeight: 600,
                        color:
                          currentTheme === t.id
                            ? 'var(--text-bright)'
                            : 'var(--text-main)',
                      }}
                    >
                      {t.name}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      {t.desc}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Backend & Runtime Connectivity */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Server size={16} color="var(--crimson-primary)" />
              <span>Backend Service Status</span>
            </div>
            <span
              className={`badge-tag ${health?.status === 'ok' ? 'emerald' : 'amber'}`}
            >
              {health?.status === 'ok' ? 'Online' : 'Checking'}
            </span>
          </div>
          <div className="card-body">
            <div style={{ marginBottom: '14px' }}>
              <label
                style={{
                  fontSize: '11px',
                  color: 'var(--text-muted)',
                  textTransform: 'uppercase',
                  fontFamily: 'var(--font-mono)',
                  display: 'block',
                  marginBottom: '6px',
                }}
              >
                API Endpoint Base URL:
              </label>
              <div
                style={{
                  padding: '8px 12px',
                  backgroundColor: 'var(--bg-input)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                  color: '#38bdf8',
                  wordBreak: 'break-all',
                }}
              >
                {API_BASE_URL}
              </div>
              <span style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '4px', display: 'block' }}>
                Configured via <code>VITE_API_BASE_URL</code> in <code>.env</code>
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                marginBottom: '16px',
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
                <span style={{ color: 'var(--text-muted)' }}>Backend App:</span>
                <span style={{ color: 'var(--text-bright)' }}>
                  {health?.app || 'FACECORE AI'}
                </span>
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
                <span style={{ color: 'var(--text-muted)' }}>Version:</span>
                <span style={{ color: 'var(--text-bright)' }}>
                  {health?.version || '0.1.0-alpha'}
                </span>
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
                <span style={{ color: 'var(--text-muted)' }}>Inference Mode:</span>
                <span style={{ color: 'var(--amber-primary)' }}>
                  {health?.engine_status || 'pending_integration'}
                </span>
              </div>
            </div>

            <button
              onClick={handleTestConnection}
              disabled={testingEndpoint}
              className="btn btn-secondary btn-sm"
              style={{ width: '100%' }}
            >
              <RefreshCw
                size={13}
                className={testingEndpoint ? 'spin-icon' : ''}
              />
              <span>{testingEndpoint ? 'Connecting...' : 'Test Backend Connection'}</span>
            </button>

            {testResult && (
              <div
                style={{
                  marginTop: '10px',
                  padding: '8px 10px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  backgroundColor: testResult.startsWith('Success')
                    ? 'var(--emerald-subtle)'
                    : 'var(--crimson-subtle)',
                  color: testResult.startsWith('Success')
                    ? 'var(--emerald-primary)'
                    : '#fda4af',
                  border: `1px solid ${
                    testResult.startsWith('Success')
                      ? 'var(--emerald-border)'
                      : 'var(--crimson-border)'
                  }`,
                }}
              >
                {testResult}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Production Operational Policy & Quality Boundaries */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">
            <Layers size={16} color="var(--crimson-primary)" />
            <span>Production Operational Policy & Calibrated Profiles (Step 10)</span>
          </div>
          <span className="badge-tag emerald">Engine Governance</span>
        </div>
        <div className="card-body">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '16px',
              marginBottom: '16px',
            }}
          >
            <div
              style={{
                padding: '14px',
                backgroundColor: 'var(--bg-input)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ color: 'var(--text-bright)', fontWeight: 600, fontSize: '13px', marginBottom: '6px' }}>
                Image Ingestion Boundaries
              </div>
              <ul style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.6', paddingLeft: '18px' }}>
                <li><strong>Hard Floor Rejection:</strong> Images &lt; 48&times;48 px rejected with HTTP 422.</li>
                <li><strong>Face Box Floor:</strong> Bounding box &lt; 16&times;16 px causes 100% FTA.</li>
                <li><strong>Advisory Quality Gate:</strong> Face width &lt; 48 px triggers score attenuation warning.</li>
                <li><strong>Safe Operating Region:</strong> Face width &ge; 128 px recommended.</li>
              </ul>
            </div>

            <div
              style={{
                padding: '14px',
                backgroundColor: 'var(--bg-input)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ color: 'var(--text-bright)', fontWeight: 600, fontSize: '13px', marginBottom: '6px' }}>
                Calibrated Threshold Profiles
              </div>
              <ul style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.6', paddingLeft: '18px' }}>
                <li><strong>High Security (&tau;=0.3600):</strong> Target FAR &le; 0.1% (3/3,000 false accepts).</li>
                <li><strong>Balanced (&tau;=0.3132):</strong> LFW Native EER calibration (FAR &approx; 0.5%).</li>
                <li><strong>High Convenience (&tau;=0.2500):</strong> Minimized false rejection under adverse conditions.</li>
                <li><strong>Custom:</strong> Manual operating threshold for specialized research.</li>
              </ul>
            </div>

            <div
              style={{
                padding: '14px',
                backgroundColor: 'var(--bg-input)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ color: 'var(--text-bright)', fontWeight: 600, fontSize: '13px', marginBottom: '6px' }}>
                Ephemeral SQLite Audit Trail
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                SQLite (WAL mode) records only non-biometric technical telemetry: SHA-256 prefixes, scalar similarity scores,
                latencies, and quality flags. Uploaded image payloads and 128-d neural embeddings are NEVER persisted to disk.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Privacy Manifesto & Architectural Guarantees */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Lock size={16} color="var(--emerald-primary)" />
            <span>Biometric Privacy & Ethical Governance Manifesto</span>
          </div>
          <span className="badge-tag emerald">Zero-Persistence Policy</span>
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
                padding: '16px',
                backgroundColor: 'var(--bg-input)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  color: 'var(--emerald-primary)',
                  fontWeight: 600,
                  fontSize: '13px',
                  marginBottom: '8px',
                }}
              >
                <ShieldCheck size={16} />
                <span>100% In-Memory Ephemeral Execution</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                Uploaded image payloads exist in ephemeral process RAM only for the duration
                of the technical check and comparison. No biometric images, templates, or
                facial embeddings are ever written to disk or secondary storage by default.
              </p>
            </div>

            <div
              style={{
                padding: '16px',
                backgroundColor: 'var(--bg-input)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  color: 'var(--emerald-primary)',
                  fontWeight: 600,
                  fontSize: '13px',
                  marginBottom: '8px',
                }}
              >
                <CheckCircle2 size={16} />
                <span>No Scraping or Surveillance Search</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                FACECORE AI contains zero web-scraping routines, reverse image searches,
                or external identity resolution crawlers. The tool is engineered strictly for
                controlled biometric evaluation between two authorized images.
              </p>
            </div>

            <div
              style={{
                padding: '16px',
                backgroundColor: 'var(--bg-input)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  color: 'var(--emerald-primary)',
                  fontWeight: 600,
                  fontSize: '13px',
                  marginBottom: '8px',
                }}
              >
                <Cpu size={16} />
                <span>Zero Telemetry or Analytics Phone-Home</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                No tracking cookies, marketing analytics, Google Analytics, or third-party
                monitoring pixels exist within this platform. All interactions remain completely
                contained inside your self-hosted environment.
              </p>
            </div>

            <div
              style={{
                padding: '16px',
                backgroundColor: 'var(--bg-input)',
                borderRadius: '8px',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  color: 'var(--amber-primary)',
                  fontWeight: 600,
                  fontSize: '13px',
                  marginBottom: '8px',
                }}
              >
                <AlertTriangle size={16} />
                <span>Probabilistic Decision Guardrails</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                A facial similarity score is never 100% proof of identity. The UI explicitly
                labels all evaluations with confidence ranges, disclaimers, and quality
                diagnostics to prevent automated or unwarranted identity verdicts.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
