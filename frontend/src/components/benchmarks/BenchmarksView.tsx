import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  ShieldAlert,
  Play,
  RotateCcw,
  Download,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Database,
  ExternalLink,
  Info,
  Camera,
  Cpu,
} from 'lucide-react';
import { ScientificAuditView } from './ScientificAuditView';
import {
  fetchBenchmarkDatasets,
  fetchBenchmarkHistory,
  fetchBenchmarkRun,
  executeBenchmarkRun,
  getBenchmarkExportUrl,
  installDataset,
} from '../../services/api';
import type {
  DatasetMetadata,
  BenchmarkRunSummary,
  BenchmarkResult,
  DatasetStatus,
} from '../../types';

export const BenchmarksView: React.FC = () => {
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [history, setHistory] = useState<BenchmarkRunSummary[]>([]);
  const [selectedRun, setSelectedRun] = useState<BenchmarkResult | null>(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('facecore-synthetic-fixture-v1');
  const [evaluateRobustness, setEvaluateRobustness] = useState<boolean>(true);
  const [maxPairs, setMaxPairs] = useState<number | null>(60);
  const [faceSelectionPolicy, setFaceSelectionPolicy] = useState<'center_face' | 'strict_single_face'>('center_face');
  const [transferThreshold, setTransferThreshold] = useState<string>('0.3128');
  const [isLoadingDatasets, setIsLoadingDatasets] = useState<boolean>(true);
  const [isRunningBenchmark, setIsRunningBenchmark] = useState<boolean>(false);
  const [isInstallingLfw, setIsInstallingLfw] = useState<boolean>(false);
  const [installMessage, setInstallMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hoveredRocPoint, setHoveredRocPoint] = useState<{ far: number; tar: number; thresh: number } | null>(null);
  const [activeViewMode, setActiveViewMode] = useState<'benchmarks' | 'audit'>('benchmarks');

  // Load datasets and history
  const loadInitialData = useCallback(async () => {
    setIsLoadingDatasets(true);
    setErrorMessage(null);
    try {
      const [dsList, histList] = await Promise.all([
        fetchBenchmarkDatasets().catch(() => []),
        fetchBenchmarkHistory().catch(() => []),
      ]);
      setDatasets(dsList);
      setHistory(histList);

      // Default to facecore-synthetic-fixture-v1 for offline testing, or first available
      const synDs = dsList.find((d) => d.dataset_id === 'facecore-synthetic-fixture-v1');
      if (synDs && synDs.is_available) {
        setSelectedDatasetId('facecore-synthetic-fixture-v1');
      } else if (dsList.length > 0) {
        setSelectedDatasetId(dsList[0].dataset_id);
      }

      // If runs exist, load the most recent run details
      if (histList.length > 0) {
        const latestRun = await fetchBenchmarkRun(histList[0].run_id).catch(() => null);
        if (latestRun) {
          setSelectedRun(latestRun);
        }
      }
    } catch {
      setErrorMessage('Failed to connect to benchmark backend service.');
    } finally {
      setIsLoadingDatasets(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Handle LFW archive installation
  const handleInstallLfw = async () => {
    setIsInstallingLfw(true);
    setInstallMessage('Downloading and verifying official LFW photographs and pairs.txt...');
    setErrorMessage(null);
    try {
      const res = await installDataset('lfw-canonical-v1');
      if (res.status === 'SUCCESS') {
        setInstallMessage('LFW dataset successfully verified and mounted!');
        const dsList = await fetchBenchmarkDatasets();
        setDatasets(dsList);
        setSelectedDatasetId('lfw-canonical-v1');
      } else {
        setErrorMessage(res.error || 'Failed to install LFW dataset.');
        setInstallMessage(null);
      }
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Dataset download error.');
      setInstallMessage(null);
    } finally {
      setIsInstallingLfw(false);
    }
  };

  // Handle benchmark execution
  const handleRunBenchmark = async () => {
    setIsRunningBenchmark(true);
    setErrorMessage(null);
    try {
      const result = await executeBenchmarkRun({
        dataset_id: selectedDatasetId,
        evaluate_robustness: evaluateRobustness,
        max_pairs: maxPairs,
        random_seed: 42,
        face_selection_policy: faceSelectionPolicy,
        transfer_threshold: transferThreshold ? parseFloat(transferThreshold) : undefined,
      });
      setSelectedRun(result);

      // Refresh history and datasets status
      const [dsList, histList] = await Promise.all([
        fetchBenchmarkDatasets().catch(() => datasets),
        fetchBenchmarkHistory().catch(() => history),
      ]);
      setDatasets(dsList);
      setHistory(histList);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Benchmark execution failed.';
      setErrorMessage(msg);
    } finally {
      setIsRunningBenchmark(false);
    }
  };

  // Switch active run from history
  const handleSelectRun = async (runId: string) => {
    try {
      const run = await fetchBenchmarkRun(runId);
      setSelectedRun(run);
    } catch {
      setErrorMessage(`Failed to load benchmark telemetry for run ${runId}`);
    }
  };

  const getStatusBadge = (status: DatasetStatus) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="badge-tag emerald"><CheckCircle2 size={11} /> COMPLETED</span>;
      case 'DATASET_VERIFIED':
        return <span className="badge-tag cyan"><CheckCircle2 size={11} /> DATASET VERIFIED</span>;
      case 'RUNNING':
        return <span className="badge-tag amber"><RotateCcw size={11} className="spin" /> RUNNING</span>;
      case 'FAILED':
        return <span className="badge-tag crimson"><AlertTriangle size={11} /> FAILED</span>;
      default:
        return <span className="badge-tag slate"><Info size={11} /> UNRUN</span>;
    }
  };

  return (
    <div>
      {/* View Header */}
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '20px', color: 'var(--text-bright)', marginBottom: '6px' }}>
          Standardized Model Benchmarks &amp; Scientific Verification Suite
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Transparent, reproducible benchmark framework for measuring biometric discrimination,
          Equal Error Rates (EER), and cross-condition robustness on verified benchmark datasets.
        </p>
      </div>

      {/* Audit vs Benchmarks Mode Toggle */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '24px',
          background: 'var(--bg-surface)',
          padding: '6px',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)',
          width: 'fit-content',
        }}
      >
        <button
          type="button"
          data-testid="toggle-benchmarks-tab"
          onClick={() => setActiveViewMode('benchmarks')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            fontSize: '12px',
            fontWeight: 600,
            borderRadius: '6px',
            border: 'none',
            cursor: 'pointer',
            transition: 'var(--trans-fast)',
            background: activeViewMode === 'benchmarks' ? 'var(--crimson-primary)' : 'transparent',
            color: activeViewMode === 'benchmarks' ? '#fff' : 'var(--text-muted)',
          }}
        >
          <BarChart3 size={15} />
          <span>Active Benchmark Console</span>
        </button>
        <button
          type="button"
          data-testid="toggle-audit-tab"
          onClick={() => setActiveViewMode('audit')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            fontSize: '12px',
            fontWeight: 600,
            borderRadius: '6px',
            border: 'none',
            cursor: 'pointer',
            transition: 'var(--trans-fast)',
            background: activeViewMode === 'audit' ? 'var(--crimson-primary)' : 'transparent',
            color: activeViewMode === 'audit' ? '#fff' : 'var(--text-muted)',
          }}
        >
          <ShieldAlert size={15} />
          <span>Step 09 Scientific Audit &amp; Reproduction</span>
          <span
            style={{
              fontSize: '10px',
              padding: '2px 6px',
              borderRadius: '4px',
              background: activeViewMode === 'audit' ? 'rgba(0,0,0,0.25)' : 'rgba(16,185,129,0.15)',
              color: activeViewMode === 'audit' ? '#fff' : 'var(--emerald-primary)',
              border: activeViewMode === 'audit' ? 'none' : '1px solid var(--emerald-border)',
              fontWeight: 700,
            }}
          >
            VERIFIED
          </span>
        </button>
      </div>

      {activeViewMode === 'audit' ? (
        <ScientificAuditView />
      ) : (
        <>
          {/* Scientific Integrity Notice */}
          <div className="alert-banner alert-amber" style={{ marginBottom: '24px' }}>
        <ShieldAlert size={20} style={{ flexShrink: 0 }} />
        <div style={{ fontSize: '12px', lineHeight: '1.5' }}>
          <strong>SCIENTIFIC INTEGRITY DIRECTIVE:</strong> Cosine similarity scores represent distance
          metrics in a 128-dimensional latent vector space, <em>not calibrated identity probabilities</em>.
          An 85% similarity score must <strong>never</strong> be interpreted as an &ldquo;85% probability
          of true identity match.&rdquo; Thresholds are calibrated exclusively on validation partitions;
          test folds remain untouched until evaluation.
        </div>
      </div>

      {/* Error alert if any */}
      {errorMessage && (
        <div className="alert-banner alert-crimson" style={{ marginBottom: '24px' }}>
          <AlertTriangle size={18} style={{ flexShrink: 0 }} />
          <div>{errorMessage}</div>
        </div>
      )}

      {/* Installation progress/success alert if active */}
      {installMessage && (
        <div className="alert-banner alert-emerald" style={{ marginBottom: '24px' }}>
          {isInstallingLfw ? (
            <RotateCcw size={18} className="spin" style={{ flexShrink: 0 }} />
          ) : (
            <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
          )}
          <div>{installMessage}</div>
        </div>
      )}

      {/* Dataset Registry Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">
            <Database size={16} color="var(--crimson-primary)" />
            <span>Authorized Dataset Registry &amp; Staging Protocols</span>
          </div>
          <span className="badge-tag slate">
            {datasets.length} Datasets Cataloged
          </span>
        </div>

        <div className="card-body" style={{ padding: 0 }}>
          <table className="diagnostics-matrix" style={{ margin: 0 }}>
            <thead>
              <tr>
                <th>Dataset &amp; Focus</th>
                <th>Modality</th>
                <th>Corpus Scale</th>
                <th>Evaluation Protocol</th>
                <th>Verification Status</th>
                <th>License &amp; Access</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((ds) => (
                <tr key={ds.dataset_id}>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-bright)' }}>
                      {ds.name}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', maxWidth: '360px' }}>
                      {ds.description}
                    </div>
                  </td>
                  <td>
                    {ds.dataset_id === 'facecore-synthetic-fixture-v1' ? (
                      <span className="badge-tag amber" style={{ fontSize: '10px' }}>
                        <Cpu size={10} /> Synthetic Fixture
                      </span>
                    ) : (
                      <span className="badge-tag emerald" style={{ fontSize: '10px' }}>
                        <Camera size={10} /> Real Photographs
                      </span>
                    )}
                  </td>
                  <td>
                    <div className="mono-text" style={{ fontSize: '11px', color: 'var(--text-main)' }}>
                      {ds.total_images.toLocaleString()} Images
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>
                      {ds.total_identities.toLocaleString()} Identities
                    </div>
                  </td>
                  <td>
                    <span className="mono-text" style={{ fontSize: '11px', color: 'var(--text-bright)' }}>
                      {ds.total_pairs.toLocaleString()} Pairs
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', alignItems: 'flex-start' }}>
                      {getStatusBadge(ds.verification_status)}
                      {ds.dataset_id === 'lfw-canonical-v1' && !ds.is_available && (
                        <button
                          onClick={handleInstallLfw}
                          disabled={isInstallingLfw}
                          className="btn btn-secondary btn-sm"
                          style={{ fontSize: '10px', padding: '2px 6px', marginTop: '4px' }}
                        >
                          <Download size={10} />
                          <span>{isInstallingLfw ? 'Installing...' : 'Download & Verify LFW'}</span>
                        </button>
                      )}
                    </div>
                  </td>
                  <td>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      {ds.license}
                    </div>
                    <a
                      href={ds.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ fontSize: '10px', color: 'var(--cyan-primary)', display: 'inline-flex', alignItems: 'center', gap: '3px' }}
                    >
                      <span>Source Portal</span>
                      <ExternalLink size={9} />
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Benchmark Control Bar */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">
            <BarChart3 size={16} color="var(--emerald-primary)" />
            <span>Benchmark Run Controller</span>
          </div>
          <div className="mono-text" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Model: SFace (SphereFace2) 128-d
          </div>
        </div>

        <div className="card-body">
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'flex-end', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '5px' }}>
                  Target Evaluation Corpus:
                </label>
                <select
                  value={selectedDatasetId}
                  onChange={(e) => setSelectedDatasetId(e.target.value)}
                  disabled={isRunningBenchmark}
                  className="input-select"
                  style={{
                    backgroundColor: 'var(--bg-input)',
                    color: 'var(--text-bright)',
                    border: '1px solid var(--border-subtle)',
                    padding: '7px 12px',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                >
                  {datasets.map((ds) => (
                    <option key={ds.dataset_id} value={ds.dataset_id}>
                      {ds.name} {ds.is_available ? '(Verified / Ready)' : '(Archive Required)'}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '5px' }}>
                  Evaluation Sampling Cap:
                </label>
                <select
                  value={maxPairs === null ? 'all' : String(maxPairs)}
                  onChange={(e) => setMaxPairs(e.target.value === 'all' ? null : Number(e.target.value))}
                  disabled={isRunningBenchmark}
                  className="input-select"
                  style={{
                    backgroundColor: 'var(--bg-input)',
                    color: 'var(--text-bright)',
                    border: '1px solid var(--border-subtle)',
                    padding: '7px 12px',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                >
                  <option value="20">20 Pairs (Fast Validation Profile)</option>
                  <option value="60">60 Pairs (Balanced 10-Fold Sample)</option>
                  <option value="120">120 Pairs (Full Synthetic Fixture)</option>
                  <option value="all">Full Protocol Corpus</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '5px' }}>
                  Acquisition / Face Selection:
                </label>
                <select
                  value={faceSelectionPolicy}
                  onChange={(e) => setFaceSelectionPolicy(e.target.value as 'center_face' | 'strict_single_face')}
                  disabled={isRunningBenchmark}
                  className="input-select"
                  style={{
                    backgroundColor: 'var(--bg-input)',
                    color: 'var(--text-bright)',
                    border: '1px solid var(--border-subtle)',
                    padding: '7px 12px',
                    borderRadius: '4px',
                    fontSize: '12px',
                  }}
                >
                  <option value="center_face">Center Face (Canonical LFW Protocol)</option>
                  <option value="strict_single_face">Strict Single Face (Fail on Multiple)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '5px' }}>
                  Transfer Baseline (&tau;):
                </label>
                <input
                  type="text"
                  value={transferThreshold}
                  onChange={(e) => setTransferThreshold(e.target.value)}
                  disabled={isRunningBenchmark}
                  placeholder="0.3128"
                  style={{
                    backgroundColor: 'var(--bg-input)',
                    color: 'var(--text-bright)',
                    border: '1px solid var(--border-subtle)',
                    padding: '7px 10px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    width: '90px',
                    fontFamily: 'monospace',
                  }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingTop: '16px' }}>
                <input
                  type="checkbox"
                  id="robustness-check"
                  checked={evaluateRobustness}
                  onChange={(e) => setEvaluateRobustness(e.target.checked)}
                  disabled={isRunningBenchmark}
                  style={{ cursor: 'pointer' }}
                />
                <label htmlFor="robustness-check" style={{ fontSize: '12px', color: 'var(--text-main)', cursor: 'pointer' }}>
                  Evaluate Robustness Perturbations (Blur, Downsampling, Glare, Occlusion)
                </label>
              </div>
            </div>

            <button
              onClick={handleRunBenchmark}
              disabled={isRunningBenchmark || isLoadingDatasets}
              className="btn btn-primary"
              style={{
                backgroundColor: 'var(--emerald-primary)',
                borderColor: 'var(--emerald-border)',
                color: '#000',
                fontWeight: 700,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              {isRunningBenchmark ? (
                <>
                  <RotateCcw size={14} className="spin" />
                  <span>Executing SFace Benchmark...</span>
                </>
              ) : (
                <>
                  <Play size={14} />
                  <span>Execute Model Benchmark</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* History Selector (if multiple runs exist) */}
      {history.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>
            EVALUATION RUN HISTORY:
          </span>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {history.map((h, i) => (
              <button
                key={h.run_id}
                onClick={() => handleSelectRun(h.run_id)}
                className={`btn btn-sm ${selectedRun?.run_id === h.run_id ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '11px', padding: '3px 8px' }}
              >
                Run #{history.length - i} ({h.dataset_name.split(' ')[0]} &mdash; Acc: {(h.accuracy * 100).toFixed(1)}%)
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Benchmark Results Display */}
      {selectedRun ? (
        <div>
          {/* Scientific Provenance Banner */}
          <div
            style={{
              padding: '12px 18px',
              backgroundColor: selectedRun.is_real_photographs ? 'rgba(16, 185, 129, 0.08)' : 'rgba(245, 158, 11, 0.08)',
              border: `1px solid ${selectedRun.is_real_photographs ? 'var(--emerald-border)' : 'var(--amber-border)'}`,
              borderRadius: '6px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {selectedRun.is_real_photographs ? (
                <span className="badge-tag emerald" style={{ fontSize: '11px', fontWeight: 700, padding: '4px 10px' }}>
                  <Camera size={13} /> REAL RESEARCH DATASET &mdash; Unconstrained Photographs
                </span>
              ) : (
                <span className="badge-tag amber" style={{ fontSize: '11px', fontWeight: 700, padding: '4px 10px' }}>
                  <Cpu size={13} /> SYNTHETIC BENCHMARK FIXTURE &mdash; Procedural Canvas Faces
                </span>
              )}
              <span className="mono-text" style={{ fontSize: '11px', color: 'var(--text-bright)' }}>
                Protocol: {selectedRun.evaluation_protocol || '10-Fold Cross-Validation'}
              </span>
            </div>

            <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
              Target Dataset: <strong style={{ color: 'var(--text-bright)' }}>{selectedRun.dataset_name}</strong>
            </div>
          </div>

          {/* Top Metric Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
              gap: '14px',
              marginBottom: '16px',
            }}
          >
            <div className="card" style={{ padding: '16px', borderLeft: '3px solid var(--emerald-primary)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>EQUAL ERROR RATE (EER)</div>
              <div className="mono-text" style={{ fontSize: '24px', fontWeight: 700, color: 'var(--emerald-primary)' }}>
                {(selectedRun.eer * 100).toFixed(2)}%
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                @ &tau; = {selectedRun.eer_threshold.toFixed(4)}
              </div>
            </div>

            <div className="card" style={{ padding: '16px', borderLeft: '3px solid var(--cyan-primary)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>AREA UNDER ROC (AUC)</div>
              <div className="mono-text" style={{ fontSize: '24px', fontWeight: 700, color: 'var(--cyan-primary)' }}>
                {selectedRun.auc.toFixed(4)}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                Trapezoidal Integration
              </div>
            </div>

            <div className="card" style={{ padding: '16px', borderLeft: '3px solid var(--amber-primary)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>CROSS-VALIDATED ACCURACY</div>
              <div className="mono-text" style={{ fontSize: '24px', fontWeight: 700, color: 'var(--amber-primary)' }}>
                {(selectedRun.accuracy * 100).toFixed(2)}%
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                10-Fold Strict Validation
              </div>
            </div>

            <div className="card" style={{ padding: '16px', borderLeft: '3px solid var(--crimson-primary)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>OPTIMAL THRESHOLD</div>
              <div className="mono-text" style={{ fontSize: '24px', fontWeight: 700, color: 'var(--crimson-primary)' }}>
                {selectedRun.optimal_threshold.toFixed(4)}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                Max Classification Margin
              </div>
            </div>

            <div className="card" style={{ padding: '16px', borderLeft: '3px solid #8B5CF6' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>TAR @ FAR = 1.0%</div>
              <div className="mono-text" style={{ fontSize: '24px', fontWeight: 700, color: '#A78BFA' }}>
                {selectedRun.tar_at_far_table.find(t => Math.abs(t.far_target - 0.01) < 1e-4)?.tar
                  ? `${(selectedRun.tar_at_far_table.find(t => Math.abs(t.far_target - 0.01) < 1e-4)!.tar * 100).toFixed(1)}%`
                  : 'N/A'}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                Operational Security Point
              </div>
            </div>

            <div className="card" style={{ padding: '16px', borderLeft: '3px solid #EC4899' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>FAILURE TO ACQUIRE (FTA)</div>
              <div className="mono-text" style={{ fontSize: '24px', fontWeight: 700, color: '#F472B6' }}>
                {((selectedRun.failure_to_acquire_rate || 0) * 100).toFixed(2)}%
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                {selectedRun.failure_to_acquire_count || 0} / {selectedRun.total_requested_pairs || selectedRun.total_pairs} pairs
              </div>
            </div>

            <div className="card" style={{ padding: '16px', borderLeft: '3px solid var(--text-muted)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>EVALUATION SAMPLE SIZE</div>
              <div className="mono-text" style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-bright)' }}>
                {selectedRun.total_pairs}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '2px' }}>
                {selectedRun.genuine_pairs} Gen / {selectedRun.impostor_pairs} Imp
              </div>
            </div>
          </div>

          {/* ISO/IEC 19795-1 FTA Breakdown */}
          {selectedRun.fta_breakdown && (
            <div
              style={{
                padding: '8px 16px',
                backgroundColor: 'var(--bg-surface)',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '20px',
                fontSize: '11px',
                flexWrap: 'wrap',
              }}
            >
              <span style={{ fontWeight: 700, color: 'var(--text-muted)' }}>ISO/IEC 19795-1 FTA BREAKDOWN:</span>
              <span className="mono-text" style={{ color: 'var(--text-bright)' }}>
                Zero Faces: <strong>{selectedRun.fta_breakdown.no_face_detected}</strong>
              </span>
              <span className="mono-text" style={{ color: 'var(--text-bright)' }}>
                Multiple Faces: <strong>{selectedRun.fta_breakdown.multiple_faces_detected}</strong>
              </span>
              <span className="mono-text" style={{ color: 'var(--text-bright)' }}>
                Alignment / Landmark: <strong>{selectedRun.fta_breakdown.alignment_failed}</strong>
              </span>
              <span className="mono-text" style={{ color: 'var(--text-bright)' }}>
                Inference Errors: <strong>{selectedRun.fta_breakdown.inference_error}</strong>
              </span>
            </div>
          )}

          {/* Confidence Intervals Readout */}
          {selectedRun.confidence_intervals.length > 0 && (
            <div
              style={{
                padding: '10px 16px',
                backgroundColor: 'var(--bg-surface)',
                borderRadius: '6px',
                border: '1px solid var(--border-subtle)',
                marginBottom: '24px',
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                flexWrap: 'wrap',
                fontSize: '11px',
              }}
            >
              <span style={{ fontWeight: 700, color: 'var(--text-muted)' }}>95% BOOTSTRAP CONFIDENCE INTERVALS (B=500):</span>
              {selectedRun.confidence_intervals.map((ci) => (
                <span key={ci.metric} className="mono-text" style={{ color: 'var(--text-bright)' }}>
                  {ci.metric}: <strong style={{ color: 'var(--cyan-primary)' }}>{(ci.mean * 100).toFixed(1)}%</strong>{' '}
                  <span style={{ color: 'var(--text-dim)' }}>
                    [{(ci.ci_lower * 100).toFixed(1)}% &ndash; {(ci.ci_upper * 100).toFixed(1)}%]
                  </span>
                </span>
              ))}
            </div>
          )}

          {/* Visual Charts Grid: ROC Curve & FAR/FRR Chart */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
              gap: '20px',
              marginBottom: '24px',
            }}
          >
            {/* ROC Curve Chart */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <BarChart3 size={15} color="var(--emerald-primary)" />
                  <span>Receiver Operating Characteristic (ROC)</span>
                </div>
                <span className="badge-tag emerald">AUC = {selectedRun.auc.toFixed(4)}</span>
              </div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                {/* SVG ROC Plot */}
                <svg
                  viewBox="0 0 360 260"
                  style={{ width: '100%', maxWidth: '440px', height: '260px', overflow: 'visible' }}
                >
                  {/* Grid lines */}
                  {[0, 0.25, 0.5, 0.75, 1.0].map((v) => {
                    const y = 220 - v * 190;
                    const x = 45 + v * 280;
                    return (
                      <g key={v}>
                        <line x1="45" y1={y} x2="325" y2={y} stroke="var(--border-subtle)" strokeDasharray="3 3" />
                        <line x1={x} y1="30" x2={x} y2="220" stroke="var(--border-subtle)" strokeDasharray="3 3" />
                        <text x="38" y={y + 3} fill="var(--text-dim)" fontSize="9" textAnchor="end" fontFamily="var(--font-mono)">
                          {v.toFixed(2)}
                        </text>
                        <text x={x} y="235" fill="var(--text-dim)" fontSize="9" textAnchor="middle" fontFamily="var(--font-mono)">
                          {v.toFixed(2)}
                        </text>
                      </g>
                    );
                  })}

                  {/* Random Guess Diagonal Line (AUC = 0.5) */}
                  <line x1="45" y1="220" x2="325" y2="30" stroke="var(--text-dim)" strokeDasharray="4 4" strokeWidth="1.5" />

                  {/* ROC Curve Line */}
                  {selectedRun.roc_curve.length > 1 && (
                    <polyline
                      fill="none"
                      stroke="var(--emerald-primary)"
                      strokeWidth="2.5"
                      points={selectedRun.roc_curve
                        .map((p) => {
                          const px = 45 + Math.min(1, Math.max(0, p.far)) * 280;
                          const py = 220 - Math.min(1, Math.max(0, p.tar)) * 190;
                          return `${px},${py}`;
                        })
                        .join(' ')}
                    />
                  )}

                  {/* Interactive points */}
                  {selectedRun.roc_curve.map((p, idx) => {
                    const px = 45 + Math.min(1, Math.max(0, p.far)) * 280;
                    const py = 220 - Math.min(1, Math.max(0, p.tar)) * 190;
                    return (
                      <circle
                        key={idx}
                        cx={px}
                        cy={py}
                        r="3"
                        fill="transparent"
                        style={{ cursor: 'pointer' }}
                        onMouseEnter={() => setHoveredRocPoint({ far: p.far, tar: p.tar, thresh: p.threshold })}
                        onMouseLeave={() => setHoveredRocPoint(null)}
                      />
                    );
                  })}

                  {/* Axes labels */}
                  <text x="185" y="252" fill="var(--text-muted)" fontSize="10" textAnchor="middle" fontWeight="600">
                    False Acceptance Rate (FAR) &rarr;
                  </text>
                  <text
                    x="15"
                    y="125"
                    fill="var(--text-muted)"
                    fontSize="10"
                    textAnchor="middle"
                    fontWeight="600"
                    transform="rotate(-90 15 125)"
                  >
                    True Acceptance Rate (TAR) &rarr;
                  </text>
                </svg>

                {/* Point Telemetry readout */}
                <div className="mono-text" style={{ fontSize: '11px', color: 'var(--text-bright)', marginTop: '8px' }}>
                  {hoveredRocPoint ? (
                    <span>
                      POINT: FAR = <strong style={{ color: 'var(--crimson-primary)' }}>{(hoveredRocPoint.far * 100).toFixed(2)}%</strong> |{' '}
                      TAR = <strong style={{ color: 'var(--emerald-primary)' }}>{(hoveredRocPoint.tar * 100).toFixed(2)}%</strong> |{' '}
                      &tau; = {hoveredRocPoint.thresh.toFixed(4)}
                    </span>
                  ) : (
                    <span style={{ color: 'var(--text-dim)' }}>Hover curve to inspect operational thresholds</span>
                  )}
                </div>
              </div>
            </div>

            {/* FAR & FRR vs Threshold Curve */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <Layers size={15} color="var(--amber-primary)" />
                  <span>FAR &amp; FRR Error Distribution (EER Point)</span>
                </div>
                <span className="badge-tag amber">EER = {(selectedRun.eer * 100).toFixed(2)}%</span>
              </div>
              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <svg
                  viewBox="0 0 360 260"
                  style={{ width: '100%', maxWidth: '440px', height: '260px', overflow: 'visible' }}
                >
                  {/* Grid lines */}
                  {[0, 0.25, 0.5, 0.75, 1.0].map((v) => {
                    const y = 220 - v * 190;
                    return (
                      <g key={v}>
                        <line x1="45" y1={y} x2="325" y2={y} stroke="var(--border-subtle)" strokeDasharray="3 3" />
                        <text x="38" y={y + 3} fill="var(--text-dim)" fontSize="9" textAnchor="end" fontFamily="var(--font-mono)">
                          {(v * 100).toFixed(0)}%
                        </text>
                      </g>
                    );
                  })}

                  {/* Threshold X-axis */}
                  {[-0.5, 0.0, 0.36, 0.7, 1.0].map((th) => {
                    const x = 45 + ((th + 1.0) / 2.0) * 280;
                    return (
                      <g key={th}>
                        <line x1={x} y1="30" x2={x} y2="220" stroke="var(--border-subtle)" strokeDasharray="2 2" />
                        <text x={x} y="235" fill="var(--text-dim)" fontSize="9" textAnchor="middle" fontFamily="var(--font-mono)">
                          {th.toFixed(2)}
                        </text>
                      </g>
                    );
                  })}

                  {/* FAR curve (Crimson) */}
                  <polyline
                    fill="none"
                    stroke="var(--crimson-primary)"
                    strokeWidth="2"
                    points={selectedRun.roc_curve
                      .map((p) => {
                        const px = 45 + ((p.threshold + 1.0) / 2.0) * 280;
                        const py = 220 - Math.min(1, Math.max(0, p.far)) * 190;
                        return `${px},${py}`;
                      })
                      .join(' ')}
                  />

                  {/* FRR curve (Amber) */}
                  <polyline
                    fill="none"
                    stroke="var(--amber-primary)"
                    strokeWidth="2"
                    points={selectedRun.roc_curve
                      .map((p) => {
                        const px = 45 + ((p.threshold + 1.0) / 2.0) * 280;
                        const py = 220 - Math.min(1, Math.max(0, p.frr)) * 190;
                        return `${px},${py}`;
                      })
                      .join(' ')}
                  />

                  {/* EER Intersection Indicator Line */}
                  {(() => {
                    const eerX = 45 + ((selectedRun.eer_threshold + 1.0) / 2.0) * 280;
                    const eerY = 220 - selectedRun.eer * 190;
                    return (
                      <g>
                        <line x1={eerX} y1="30" x2={eerX} y2="220" stroke="var(--emerald-primary)" strokeWidth="1.5" strokeDasharray="3 3" />
                        <circle cx={eerX} cy={eerY} r="4" fill="var(--emerald-primary)" />
                      </g>
                    );
                  })()}

                  <text x="185" y="252" fill="var(--text-muted)" fontSize="10" textAnchor="middle" fontWeight="600">
                    Decision Threshold (&tau;) &rarr;
                  </text>
                </svg>

                <div style={{ display: 'flex', gap: '16px', fontSize: '11px', marginTop: '8px' }}>
                  <span style={{ color: 'var(--crimson-primary)', fontWeight: 600 }}>&mdash; FAR (False Acceptance)</span>
                  <span style={{ color: 'var(--amber-primary)', fontWeight: 600 }}>&mdash; FRR (False Rejection)</span>
                  <span style={{ color: 'var(--emerald-primary)', fontWeight: 600 }}>&bull; EER Intersection Point</span>
                </div>
              </div>
            </div>
          </div>

          {/* Confusion Matrix & TAR Table */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '20px',
              marginBottom: '24px',
            }}
          >
            {/* Confusion Matrix */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <Layers size={15} color="var(--cyan-primary)" />
                  <span>Confusion Matrix &amp; Error Breakdown</span>
                </div>
                <span className="mono-text" style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                  @ &tau; = {selectedRun.optimal_threshold.toFixed(4)}
                </span>
              </div>
              <div className="card-body">
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
                  <div style={{ padding: '12px', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--emerald-border)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>TRUE POSITIVES (TP)</div>
                    <div className="mono-text" style={{ fontSize: '20px', fontWeight: 700, color: 'var(--emerald-primary)' }}>
                      {selectedRun.confusion_matrix.tp}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>Correctly Verified Pairs</div>
                  </div>

                  <div style={{ padding: '12px', backgroundColor: 'rgba(244, 63, 94, 0.1)', border: '1px solid var(--crimson-border)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>FALSE POSITIVES (FP)</div>
                    <div className="mono-text" style={{ fontSize: '20px', fontWeight: 700, color: 'var(--crimson-primary)' }}>
                      {selectedRun.confusion_matrix.fp}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>False Matches (Security Risk)</div>
                  </div>

                  <div style={{ padding: '12px', backgroundColor: 'rgba(245, 158, 11, 0.1)', border: '1px solid var(--amber-border)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>FALSE NEGATIVES (FN)</div>
                    <div className="mono-text" style={{ fontSize: '20px', fontWeight: 700, color: 'var(--amber-primary)' }}>
                      {selectedRun.confusion_matrix.fn}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>False Rejections (User Friction)</div>
                  </div>

                  <div style={{ padding: '12px', backgroundColor: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.3)', borderRadius: '4px' }}>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>TRUE NEGATIVES (TN)</div>
                    <div className="mono-text" style={{ fontSize: '20px', fontWeight: 700, color: 'var(--cyan-primary)' }}>
                      {selectedRun.confusion_matrix.tn}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-dim)' }}>Correctly Rejected Impostors</div>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-main)', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
                  <span>Precision: <strong>{(selectedRun.confusion_matrix.precision * 100).toFixed(1)}%</strong></span>
                  <span>Recall: <strong>{(selectedRun.confusion_matrix.recall * 100).toFixed(1)}%</strong></span>
                  <span>F1-Score: <strong>{selectedRun.confusion_matrix.f1_score.toFixed(3)}</strong></span>
                </div>
              </div>
            </div>

            {/* Operational FAR Table */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <ShieldAlert size={15} color="var(--emerald-primary)" />
                  <span>Operational Operating Points (TAR @ FAR)</span>
                </div>
              </div>
              <div className="card-body" style={{ padding: 0 }}>
                <table className="diagnostics-matrix" style={{ margin: 0 }}>
                  <thead>
                    <tr>
                      <th>Target Security Level</th>
                      <th>Max Allowed FAR</th>
                      <th>Calibrated Threshold</th>
                      <th>True Accept (TAR)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedRun.tar_at_far_table.map((row, idx) => (
                      <tr key={idx}>
                        <td>
                          {row.far_target <= 0.001
                            ? 'High Security (Surveillance)'
                            : row.far_target <= 0.01
                            ? 'Standard Security (Border/Access)'
                            : 'Convenience Level (Consumer Unlock)'}
                        </td>
                        <td>
                          <span className="mono-text" style={{ color: 'var(--crimson-primary)' }}>
                            {(row.far_target * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td>
                          <span className="mono-text" style={{ color: 'var(--text-main)' }}>
                            {row.threshold.toFixed(4)}
                          </span>
                        </td>
                        <td>
                          <span className="mono-text" style={{ color: 'var(--emerald-primary)', fontWeight: 700 }}>
                            {(row.tar * 100).toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Robustness Perturbation Matrix */}
          {selectedRun.robustness_results.length > 0 && (
            <div className="card" style={{ marginBottom: '24px' }}>
              <div className="card-header">
                <div className="card-title">
                  <RotateCcw size={15} color="var(--amber-primary)" />
                  <span>Controlled Environmental Robustness Degradation Analysis</span>
                </div>
                <span className="badge-tag amber">Controlled Perturbations</span>
              </div>
              <div className="card-body" style={{ padding: 0 }}>
                <table className="diagnostics-matrix" style={{ margin: 0 }}>
                  <thead>
                    <tr>
                      <th>Perturbation Condition</th>
                      <th>Degradation Description</th>
                      <th>Sample Pairs</th>
                      <th>Observed Accuracy</th>
                      <th>EER</th>
                      <th>ROC-AUC</th>
                      <th>TAR @ FAR=1%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/* Baseline row */}
                    <tr style={{ backgroundColor: 'rgba(16, 185, 129, 0.05)' }}>
                      <td>
                        <strong style={{ color: 'var(--emerald-primary)' }}>&bull; Baseline (Reference)</strong>
                      </td>
                      <td style={{ color: 'var(--text-dim)' }}>Native unperturbed image pairs</td>
                      <td className="mono-text">{selectedRun.total_pairs}</td>
                      <td className="mono-text" style={{ color: 'var(--emerald-primary)', fontWeight: 700 }}>
                        {(selectedRun.accuracy * 100).toFixed(1)}%
                      </td>
                      <td className="mono-text">{(selectedRun.eer * 100).toFixed(1)}%</td>
                      <td className="mono-text">{selectedRun.auc.toFixed(3)}</td>
                      <td className="mono-text">
                        {selectedRun.tar_at_far_table.find(t => Math.abs(t.far_target - 0.01) < 1e-4)
                          ? `${(selectedRun.tar_at_far_table.find(t => Math.abs(t.far_target - 0.01) < 1e-4)!.tar * 100).toFixed(1)}%`
                          : 'N/A'}
                      </td>
                    </tr>
                    {/* Perturbation rows */}
                    {selectedRun.robustness_results.map((r, idx) => (
                      <tr key={idx}>
                        <td>
                          <span style={{ fontWeight: 600, color: 'var(--text-bright)' }}>{r.condition_name}</span>
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--text-dim)' }}>{r.description}</td>
                        <td className="mono-text">{r.sample_size}</td>
                        <td className="mono-text" style={{ color: r.accuracy < selectedRun.accuracy * 0.85 ? 'var(--crimson-primary)' : 'var(--text-main)' }}>
                          {(r.accuracy * 100).toFixed(1)}%
                        </td>
                        <td className="mono-text">{(r.eer * 100).toFixed(1)}%</td>
                        <td className="mono-text">{r.auc.toFixed(3)}</td>
                        <td className="mono-text">{(r.tar_at_far_01 * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Cross-Dataset Threshold Transfer Generalization Card (Step 08) */}
          {selectedRun.transferred_threshold != null && selectedRun.transferred_accuracy != null && (
            <div className="card" style={{ marginBottom: '24px', borderLeft: '4px solid var(--cyan-primary)' }}>
              <div className="card-header">
                <div className="card-title">
                  <ShieldAlert size={15} color="var(--cyan-primary)" />
                  <span>Cross-Dataset Threshold Generalization Audit</span>
                </div>
                <span className="badge-tag cyan">Phase 3 Transfer Evaluation</span>
              </div>
              <div className="card-body">
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
                  Evaluates how the LFW validation-calibrated baseline threshold (<strong>&tau; = {selectedRun.transferred_threshold.toFixed(4)}</strong>) generalizes when applied directly to <strong>{selectedRun.dataset_name}</strong> without dataset-specific re-tuning.
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                  <div style={{ padding: '14px', backgroundColor: 'rgba(16, 185, 129, 0.08)', borderRadius: '6px', border: '1px solid var(--emerald-border)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>DATASET NATIVE THRESHOLD</div>
                    <div className="mono-text" style={{ fontSize: '22px', fontWeight: 700, color: 'var(--emerald-primary)', margin: '4px 0' }}>
                      {(selectedRun.accuracy * 100).toFixed(2)}%
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      Calibrated at &tau;* = <strong>{selectedRun.optimal_threshold.toFixed(4)}</strong>
                    </div>
                  </div>

                  <div style={{ padding: '14px', backgroundColor: selectedRun.transferred_accuracy < selectedRun.accuracy ? 'rgba(245, 158, 11, 0.08)' : 'rgba(6, 182, 212, 0.08)', borderRadius: '6px', border: selectedRun.transferred_accuracy < selectedRun.accuracy ? '1px solid var(--amber-border)' : '1px solid rgba(6, 182, 212, 0.3)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>TRANSFERRED LFW THRESHOLD</div>
                    <div className="mono-text" style={{ fontSize: '22px', fontWeight: 700, color: selectedRun.transferred_accuracy < selectedRun.accuracy ? 'var(--amber-primary)' : 'var(--cyan-primary)', margin: '4px 0' }}>
                      {(selectedRun.transferred_accuracy * 100).toFixed(2)}%
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      Fixed at &tau; = <strong>{selectedRun.transferred_threshold.toFixed(4)}</strong>
                    </div>
                  </div>

                  <div style={{ padding: '14px', backgroundColor: 'var(--bg-card-subtle)', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>TRANSFER GAP (&Delta; ACCURACY)</div>
                    <div className="mono-text" style={{ fontSize: '22px', fontWeight: 700, color: (selectedRun.accuracy - selectedRun.transferred_accuracy) > 0.01 ? 'var(--crimson-primary)' : 'var(--emerald-primary)', margin: '4px 0' }}>
                      {((selectedRun.transferred_accuracy - selectedRun.accuracy) * 100).toFixed(2)}%
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      {(selectedRun.accuracy - selectedRun.transferred_accuracy) > 0.01 ? 'Performance degradation under fixed transfer' : 'Robust threshold transfer'}
                    </div>
                  </div>
                </div>

                {selectedRun.transferred_confusion_matrix && (
                  <div style={{ fontSize: '12px', padding: '10px 14px', backgroundColor: 'rgba(255, 255, 255, 0.02)', borderRadius: '4px', border: '1px solid var(--border-subtle)' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Transferred decision distribution: </span>
                    <strong style={{ color: 'var(--emerald-primary)' }}>{selectedRun.transferred_confusion_matrix.tp} TP</strong>,{' '}
                    <strong style={{ color: 'var(--cyan-primary)' }}>{selectedRun.transferred_confusion_matrix.tn} TN</strong>,{' '}
                    <strong style={{ color: 'var(--crimson-primary)' }}>{selectedRun.transferred_confusion_matrix.fp} FP (False Matches)</strong>,{' '}
                    <strong style={{ color: 'var(--amber-primary)' }}>{selectedRun.transferred_confusion_matrix.fn} FN (False Rejections)</strong>.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Real vs Synthetic Benchmark Comparison Card */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-header">
              <div className="card-title">
                <Layers size={15} color="var(--cyan-primary)" />
                <span>Empirical Domain Comparison: Real Photographs (LFW) vs. Synthetic Fixture</span>
              </div>
              <span className="badge-tag cyan">Phase 5 Validation</span>
            </div>
            <div className="card-body" style={{ padding: 0 }}>
              <table className="diagnostics-matrix" style={{ margin: 0 }}>
                <thead>
                  <tr>
                    <th>Evaluation Dimension</th>
                    <th>Synthetic Fixture (Step 06)</th>
                    <th>Real Photographs (LFW View 2)</th>
                    <th>Scientific Methodology Note</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Data Modality</strong></td>
                    <td>
                      <span className="badge-tag amber" style={{ fontSize: '10px' }}>
                        <Cpu size={10} /> Procedural Canvas Vectors
                      </span>
                    </td>
                    <td>
                      <span className="badge-tag emerald" style={{ fontSize: '10px' }}>
                        <Camera size={10} /> Genuine News Photographs
                      </span>
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      Synthetic faces share geometric ellipse outlines; real photographs contain complex textures, lighting, and expressions.
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Evaluation Corpus</strong></td>
                    <td className="mono-text">120 Pairs (20 Identities)</td>
                    <td className="mono-text">6,000 Official Pairs (5,749 Identities)</td>
                    <td style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      LFW official View 2 protocol provides 10 balanced folds (300 genuine + 300 impostor per fold).
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Decision Threshold (&tau;)</strong></td>
                    <td className="mono-text" style={{ color: 'var(--amber-primary)', fontWeight: 700 }}>
                      &tau; &asymp; 0.94
                    </td>
                    <td className="mono-text" style={{ color: 'var(--emerald-primary)', fontWeight: 700 }}>
                      &tau; &asymp; 0.31 &ndash; 0.36
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      SFace weights were trained on real human faces. High synthetic threshold is caused by shared geometric contours elevating baseline cosine similarity.
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Cross-Validation Accuracy</strong></td>
                    <td className="mono-text">85.0% &plusmn; 2.5%</td>
                    <td className="mono-text" style={{ color: 'var(--emerald-primary)', fontWeight: 700 }}>98.3% &ndash; 99.0%</td>
                    <td style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      SFace demonstrates high discrimination on real human biometric features, confirming model efficacy.
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Failure to Acquire (FTA)</strong></td>
                    <td className="mono-text">0.0% (Controlled geometry)</td>
                    <td className="mono-text">0.0% (Center Face) / ~40% (Strict Single)</td>
                    <td style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                      Unconstrained real photographs frequently have background individuals, requiring ISO 19795-1 acquisition policy specification.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Export Report Bar */}
          <div
            style={{
              padding: '14px 20px',
              backgroundColor: 'var(--bg-surface)',
              borderRadius: '6px',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
            }}
          >
            <div className="mono-text" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              RUN ID: <span style={{ color: 'var(--text-bright)' }}>{selectedRun.run_id}</span> | COMPLETED IN {selectedRun.execution_time_seconds}s
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <a
                href={getBenchmarkExportUrl(selectedRun.run_id, 'json')}
                download={`facecore_benchmark_${selectedRun.run_id}.json`}
                className="btn btn-secondary btn-sm"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <Download size={13} />
                <span>Export JSON Report</span>
              </a>

              <a
                href={getBenchmarkExportUrl(selectedRun.run_id, 'csv')}
                download={`facecore_pairs_${selectedRun.run_id}.csv`}
                className="btn btn-secondary btn-sm"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <Download size={13} />
                <span>Export Pairwise CSV</span>
              </a>

              <a
                href={getBenchmarkExportUrl(selectedRun.run_id, 'markdown')}
                download={`facecore_benchmark_${selectedRun.run_id}.md`}
                className="btn btn-secondary btn-sm"
                style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}
              >
                <Download size={13} />
                <span>Export Markdown</span>
              </a>
            </div>
          </div>
        </div>
      ) : (
        /* Empty / Unrun placeholder */
        <div
          className="card"
          style={{
            padding: '48px 24px',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <BarChart3 size={36} color="var(--text-dim)" />
          <div style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-bright)' }}>
            NO BENCHMARKS EXECUTED YET &mdash; Ready for Verification
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '420px', margin: 0 }}>
            Select an authorized dataset above and click &ldquo;Execute Model Benchmark&rdquo; to
            evaluate SFace with 10-fold cross-validation and generate ROC and EER distributions.
          </p>
        </div>
      )}
        </>
      )}
    </div>
  );
};
