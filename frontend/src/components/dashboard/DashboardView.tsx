import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  ShieldCheck,
  Cpu,
  Database,
  CheckCircle2,
  Clock,
  RefreshCw,
  Trash2,
  ScanFace,
  Layers,
} from 'lucide-react';
import type { DashboardStatsResponse, ComparisonHistoryRecord, ReadinessResponse, NavTab } from '../../types';
import { fetchDashboardStats, fetchComparisonHistory, clearComparisonHistory, fetchReadiness } from '../../services/api';

interface DashboardViewProps {
  onNavigate: (tab: NavTab) => void;
  onShowToast: (msg: {
    type: 'success' | 'error' | 'info' | 'warning';
    message: string;
    title?: string;
  }) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate, onShowToast }) => {
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [history, setHistory] = useState<ComparisonHistoryRecord[]>([]);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isClearing, setIsClearing] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    try {
      const [s, h, r] = await Promise.all([
        fetchDashboardStats(),
        fetchComparisonHistory(15),
        fetchReadiness(),
      ]);
      setStats(s);
      setHistory(h);
      setReadiness(r);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch dashboard telemetry';
      onShowToast({
        type: 'error',
        title: 'Telemetry Fetch Error',
        message: msg,
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [onShowToast]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, [loadData]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadData();
  };

  const handleClearHistory = async () => {
    if (!window.confirm('Clear all historical comparison audit records from the local SQLite database?')) {
      return;
    }
    setIsClearing(true);
    try {
      const res = await clearComparisonHistory();
      onShowToast({
        type: 'info',
        title: 'Audit Log Cleared',
        message: `Deleted ${res.deleted} comparison log entries.`,
      });
      loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to clear history';
      onShowToast({
        type: 'error',
        title: 'Operation Failed',
        message: msg,
      });
    } finally {
      setIsClearing(false);
    }
  };

  const matchRate = stats && stats.total_comparisons > 0
    ? ((stats.successful_matches / stats.total_comparisons) * 100).toFixed(1)
    : '0.0';

  const nonMatchRate = stats && stats.total_comparisons > 0
    ? ((stats.successful_non_matches / stats.total_comparisons) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="dashboard-container" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header & Actions */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '20px', color: 'var(--text-bright)', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={20} color="var(--crimson-primary)" />
            <span>Production Biometric Audit Dashboard</span>
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Real-time biometric engine telemetry, SQLite audit trail, and operational failure-to-acquire metrics.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="btn btn-secondary btn-sm"
            title="Refresh SQLite telemetry"
          >
            <RefreshCw size={13} className={isRefreshing ? 'spin-icon' : ''} />
            <span>{isRefreshing ? 'Refreshing...' : 'Refresh Telemetry'}</span>
          </button>

          <button
            onClick={() => onNavigate('compare')}
            className="btn btn-primary btn-sm"
          >
            <ScanFace size={14} />
            <span>Launch Evaluation</span>
          </button>
        </div>
      </div>

      {/* Engine & Readiness Status Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '12px',
          padding: '12px 16px',
          backgroundColor: 'var(--bg-input)',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Cpu size={18} color="var(--emerald-primary)" />
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Inference Pipeline</div>
            <div style={{ fontSize: '13px', color: 'var(--text-bright)', fontWeight: 600 }}>
              YuNet + SFace (CPU INT8/FP32)
            </div>
          </div>
          <span className="badge-tag emerald" style={{ marginLeft: 'auto' }}>
            {readiness?.models_loaded ? 'READY' : 'OFFLINE'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Database size={18} color="var(--crimson-primary)" />
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Persistence Store</div>
            <div style={{ fontSize: '13px', color: 'var(--text-bright)', fontWeight: 600 }}>
              SQLite (WAL Mode, Schema v{stats?.schema_version || 1})
            </div>
          </div>
          <span className="badge-tag slate" style={{ marginLeft: 'auto' }}>
            {readiness?.database_connected ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldCheck size={18} color="var(--emerald-primary)" />
          <div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Biometric Privacy Policy</div>
            <div style={{ fontSize: '13px', color: 'var(--emerald-primary)', fontWeight: 600 }}>
              100% Ephemeral RAM Only
            </div>
          </div>
          <span className="badge-tag emerald" style={{ marginLeft: 'auto', fontSize: '9px' }}>
            NO IMAGES SAVED
          </span>
        </div>
      </div>

      {/* Hero Metric Cards */}
      <div
        className="results-hero-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
          gap: '16px',
        }}
      >
        {/* Total Comparisons */}
        <div className="stat-metric-box">
          <span className="stat-label">Total Comparisons</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
            <span className="stat-val mono-text" style={{ fontSize: '26px', color: 'var(--text-bright)' }}>
              {isLoading ? '...' : (stats?.total_comparisons ?? 0)}
            </span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>audited events</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
            Logged in SQLite audit table
          </span>
        </div>

        {/* Matches */}
        <div className="stat-metric-box">
          <span className="stat-label">Verified Matches</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
            <span className="stat-val mono-text" style={{ fontSize: '26px', color: 'var(--emerald-primary)' }}>
              {isLoading ? '...' : (stats?.successful_matches ?? 0)}
            </span>
            <span style={{ fontSize: '11px', color: 'var(--emerald-primary)' }}>({matchRate}%)</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Above active threshold
          </span>
        </div>

        {/* Non-Matches */}
        <div className="stat-metric-box">
          <span className="stat-label">Verified Non-Matches</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
            <span className="stat-val mono-text" style={{ fontSize: '26px', color: 'var(--amber-primary)' }}>
              {isLoading ? '...' : (stats?.successful_non_matches ?? 0)}
            </span>
            <span style={{ fontSize: '11px', color: 'var(--amber-primary)' }}>({nonMatchRate}%)</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Below active threshold
          </span>
        </div>

        {/* Avg Latency */}
        <div className="stat-metric-box">
          <span className="stat-label">Mean Inference Latency</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
            <span className="stat-val mono-text" style={{ fontSize: '26px', color: '#38bdf8' }}>
              {isLoading ? '...' : (stats?.average_latency_ms ? stats.average_latency_ms.toFixed(1) : '0.0')}
            </span>
            <span style={{ fontSize: '11px', color: '#38bdf8' }}>ms / pair</span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Detection + Alignment + SFace
          </span>
        </div>

        {/* Failure to Acquire */}
        <div className="stat-metric-box">
          <span className="stat-label">Failure to Acquire (FTA)</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '6px' }}>
            <span
              className="stat-val mono-text"
              style={{
                fontSize: '26px',
                color: (stats?.fta_rate_percent ?? 0) > 5 ? 'var(--crimson-primary)' : 'var(--text-bright)',
              }}
            >
              {isLoading ? '...' : (stats?.fta_rate_percent ? stats.fta_rate_percent.toFixed(2) : '0.00')}%
            </span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              ({stats?.total_fta_events ?? 0} events)
            </span>
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Canvas &lt;48px or face &lt;16px
          </span>
        </div>
      </div>

      {/* Operational Policy & FTA Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '16px' }}>
        {/* Step 10 Operational Policy Card */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <Layers size={16} color="var(--crimson-primary)" />
              <span>Step 10 Operating Policy & Threshold Profiles</span>
            </div>
            <span className="badge-tag emerald">Active Policy</span>
          </div>
          <div className="card-body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div
                style={{
                  padding: '10px',
                  backgroundColor: 'var(--bg-input)',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-bright)', fontSize: '13px' }}>
                    High Security Profile
                  </span>
                  <span className="mono-text" style={{ color: 'var(--crimson-primary)', fontWeight: 600 }}>
                    &tau; = 0.3600
                  </span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Target FAR &le; 0.1% (3 false accepts per 3,000 impostor comparisons). Recommended for access control.
                </p>
              </div>

              <div
                style={{
                  padding: '10px',
                  backgroundColor: 'var(--bg-input)',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-bright)', fontSize: '13px' }}>
                    Balanced Profile (LFW Native)
                  </span>
                  <span className="mono-text" style={{ color: 'var(--emerald-primary)', fontWeight: 600 }}>
                    &tau; = 0.3132
                  </span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  EER operating point calibrated across 10-fold LFW View 2 evaluation (FAR &approx; 0.5%, FRR &approx; 2.5%).
                </p>
              </div>

              <div
                style={{
                  padding: '10px',
                  backgroundColor: 'var(--bg-input)',
                  borderRadius: '6px',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-bright)', fontSize: '13px' }}>
                    High Convenience Profile
                  </span>
                  <span className="mono-text" style={{ color: '#38bdf8', fontWeight: 600 }}>
                    &tau; = 0.2500
                  </span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                  Prioritizes low false rejection under challenging conditions (pose, lighting, compression).
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quality Gates & Diagnostics Summary */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <ShieldCheck size={16} color="var(--emerald-primary)" />
              <span>Ingestion Gates & Failure Telemetry</span>
            </div>
            <span className="badge-tag slate">Quality Rules</span>
          </div>
          <div className="card-body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Hard Floor Gate (Rejection)</span>
                <span className="mono-text" style={{ color: 'var(--crimson-primary)', fontWeight: 600 }}>&lt; 48&times;48 px</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Face Box Floor (100% FTA Risk)</span>
                <span className="mono-text" style={{ color: 'var(--crimson-primary)', fontWeight: 600 }}>&lt; 16&times;16 px</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Soft Quality Advisory Gate</span>
                <span className="mono-text" style={{ color: 'var(--amber-primary)', fontWeight: 600 }}>Face width &lt; 48 px</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Safe Operational Boundary</span>
                <span className="mono-text" style={{ color: 'var(--emerald-primary)', fontWeight: 600 }}>&ge; 128&times;128 px</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0' }}>
                <span style={{ color: 'var(--text-muted)' }}>Audit Log DB Size on Disk</span>
                <span className="mono-text" style={{ color: '#38bdf8' }}>
                  {stats ? (stats.database_size_bytes / 1024).toFixed(1) + ' KB' : '0 KB'}
                </span>
              </div>
            </div>

            <div
              style={{
                marginTop: '12px',
                padding: '8px 10px',
                backgroundColor: 'var(--bg-input)',
                borderRadius: '6px',
                fontSize: '11px',
                color: 'var(--text-dim)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <CheckCircle2 size={13} color="var(--emerald-primary)" />
              <span>Zero-Storage Guarantee: No facial crops or 128-d vectors are stored on disk.</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Comparison Audit Log Table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Clock size={16} color="var(--crimson-primary)" />
            <span>Cryptographic Audit Trail (Recent Evaluations)</span>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {history.length > 0 && (
              <button
                onClick={handleClearHistory}
                disabled={isClearing}
                className="btn btn-secondary btn-sm"
                title="Clear SQLite comparison audit records"
              >
                <Trash2 size={13} />
                <span>{isClearing ? 'Clearing...' : 'Clear Audit Log'}</span>
              </button>
            )}
          </div>
        </div>

        <div className="card-body" style={{ padding: '0' }}>
          {history.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-dim)' }}>
              <ScanFace size={32} style={{ margin: '0 auto 12px', opacity: 0.4 }} />
              <p style={{ fontSize: '13px' }}>No comparison evaluations recorded yet in the audit log.</p>
              <button
                onClick={() => onNavigate('compare')}
                className="btn btn-primary btn-sm"
                style={{ marginTop: '12px' }}
              >
                Launch First Comparison
              </button>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="diagnostics-matrix" style={{ margin: 0, width: '100%' }}>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Probe SHA-256</th>
                    <th>Ref SHA-256</th>
                    <th>Profile</th>
                    <th>Threshold</th>
                    <th>Cosine Score</th>
                    <th>Verdict</th>
                    <th>Latency</th>
                    <th>Advisory</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((rec) => {
                    const isMatch = rec.decision === 'MATCH';
                    const isFta = rec.status === 'FAILED';
                    const score = rec.similarity_score;

                    return (
                      <tr key={rec.id}>
                        <td style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                          {new Date(rec.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </td>
                        <td className="mono-text" style={{ fontSize: '11px', color: '#38bdf8' }}>
                          {rec.probe_hash_prefix || '—'}
                        </td>
                        <td className="mono-text" style={{ fontSize: '11px', color: '#38bdf8' }}>
                          {rec.reference_hash_prefix || '—'}
                        </td>
                        <td>
                          <span className="badge-tag slate" style={{ textTransform: 'capitalize', fontSize: '10px' }}>
                            {rec.threshold_profile.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="mono-text" style={{ fontSize: '11px' }}>
                          &tau; = {rec.threshold_used.toFixed(4)}
                        </td>
                        <td className="mono-text" style={{ fontSize: '12px', fontWeight: 600 }}>
                          {score !== null ? (
                            <span style={{ color: isMatch ? 'var(--emerald-primary)' : 'var(--amber-primary)' }}>
                              {score >= 0 ? `+${score.toFixed(4)}` : score.toFixed(4)}
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-dim)' }}>N/A</span>
                          )}
                        </td>
                        <td>
                          {isFta ? (
                            <span className="badge-tag crimson" style={{ fontSize: '10px' }}>
                              FTA
                            </span>
                          ) : isMatch ? (
                            <span className="badge-tag emerald" style={{ fontSize: '10px' }}>
                              MATCH
                            </span>
                          ) : (
                            <span className="badge-tag amber" style={{ fontSize: '10px' }}>
                              NO MATCH
                            </span>
                          )}
                        </td>
                        <td className="mono-text" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {rec.inference_latency_ms !== null ? `${rec.inference_latency_ms.toFixed(1)} ms` : '—'}
                        </td>
                        <td>
                          {rec.has_quality_warnings ? (
                            <span className="badge-tag amber" style={{ fontSize: '9px' }}>
                              Quality Flag
                            </span>
                          ) : (
                            <span className="badge-tag emerald" style={{ fontSize: '9px' }}>
                              Clean
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
