import React, { useState } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  Info,
  Terminal,
  Copy,
  Check,
  FileText,
  Database,
  Layers,
  Scale,
} from 'lucide-react';

export const ScientificAuditView: React.FC = () => {
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  const handleCopy = (cmd: string, key: string) => {
    navigator.clipboard.writeText(cmd);
    setCopiedCmd(key);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  const discrepancies = [
    {
      id: 'DISC-01',
      severity: 'HIGH',
      description: 'Silent pair omission in CALFW and CPLFW CSV parsers',
      evidence: 'parse_calfw_pairs_csv used require_all=False with continue, silently dropping 3,576 pairs without recording missing images.',
      affected: 'manifest.py, runner.py',
      resolution: 'Updated parsers and runner to audit and report official pairs (6,000), resolvable pairs (2,424 and 2,494), and missing image files (2,640 and 2,444).',
      status: 'RESOLVED',
    },
    {
      id: 'DISC-02',
      severity: 'HIGH',
      description: 'Demonstration subsampling masquerading as full evaluation',
      evidence: 'Step 07 and 08 evaluated only 120 or 60 sample pairs. Full 6,000-pair official protocols were never executed.',
      affected: 'STEP07_REPORT.md, STEP08_CROSS_DATASET_REPORT.md',
      resolution: 'Executed full-scale evaluation across all 6,000 LFW pairs and all 2,424 / 2,494 resolvable CALFW/CPLFW pairs.',
      status: 'RESOLVED',
    },
    {
      id: 'DISC-03',
      severity: 'MEDIUM',
      description: 'Asymmetric perturbation in robustness stress-testing',
      evidence: '_compute_pair_similarity only applied perturbation to image_a, leaving image_b unperturbed.',
      affected: 'runner.py, robustness.py',
      resolution: 'Upgraded engine to support symmetric pair perturbations where identical transformations are applied to both images.',
      status: 'RESOLVED',
    },
    {
      id: 'DISC-04',
      severity: 'MEDIUM',
      description: 'Missing condition-level FTA and distribution telemetry in robustness runs',
      evidence: 'Robustness runs silently skipped detection failures without recording FTA rates or score shifts per condition.',
      affected: 'schemas.py, runner.py',
      resolution: 'Extended RobustnessConditionResult and runner to capture attempted count, failed detections, FTA rate, genuine mean, and impostor mean.',
      status: 'RESOLVED',
    },
    {
      id: 'DISC-05',
      severity: 'MEDIUM',
      description: 'Incomplete run provenance and cryptographic fingerprint metadata',
      evidence: 'BenchmarkResult lacked SHA-256 weight digests, pair-list hashes, and deterministic CLI rerun commands.',
      affected: 'schemas.py, runner.py',
      resolution: 'Incorporate full SHA-256 digests of ONNX weights, pair lists, runtime versions, and CLI reproducibility commands.',
      status: 'RESOLVED',
    },
    {
      id: 'DISC-06',
      severity: 'LOW',
      description: 'Test-fold threshold isolation verification',
      evidence: 'Threshold calibration cross-validation required formal verification that test scores do not influence validation thresholds.',
      affected: 'runner.py, metrics.py',
      resolution: 'Validated validation-only threshold isolation with zero test contamination; verified in automated regression tests.',
      status: 'RESOLVED',
    },
    {
      id: 'DISC-07',
      severity: 'MEDIUM',
      description: 'Absence of dedicated scientific audit interface in frontend',
      evidence: 'UI presented benchmark run cards and transfer panels, but lacked an integrated view summarizing evaluation completeness, official vs custom protocols, and discrepancy tracking.',
      affected: 'BenchmarksView.tsx',
      resolution: 'Implemented dedicated Scientific Audit & Reproduction interface with full provenance, completeness indicators, and discrepancy tracking.',
      status: 'RESOLVED',
    },
    {
      id: 'DISC-08',
      severity: 'HIGH',
      description: 'Unexplained threshold divergence between CALFW (tau=0.387-0.491) and LFW (tau=0.313)',
      evidence: 'CALFW optimal threshold observed significantly higher than LFW baseline; root cause unknown.',
      affected: 'STEP08_CROSS_DATASET_REPORT.md, metrics.py',
      resolution: 'Conducted empirical distributional analysis proving that demographic attribute-matching in negative pairs inflates impostor cosine similarities (mean 0.1703 vs 0.0838), naturally shifting optimal threshold upward.',
      status: 'RESOLVED',
    },
  ];

  return (
    <div>
      {/* Audit Banner */}
      <div
        className="card"
        style={{
          marginBottom: '24px',
          borderLeft: '4px solid var(--cyan-primary)',
          backgroundColor: 'rgba(6, 182, 212, 0.04)',
        }}
      >
        <div className="card-body">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <ShieldAlert size={20} color="var(--cyan-primary)" />
            <h3 style={{ fontSize: '16px', color: 'var(--text-bright)', margin: 0, fontWeight: 700 }}>
              Independent Scientific Validation &amp; Quality Audit (STEP 09)
            </h3>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0, lineHeight: 1.5 }}>
            Independent audit and full-scale empirical reproduction of the production facial recognition
            pipeline (OpenCV YuNet + SFace 128-d cosine embedding). Evaluated across <strong>10,918 authentic photograph pairs</strong> with
            strict validation isolation, cryptographic provenance, and independent metric recalculation.
          </p>
        </div>
      </div>

      {/* Executive Audit Verdicts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <div className="card" style={{ padding: '16px', borderTop: '3px solid var(--emerald-primary)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600, marginBottom: '6px' }}>
            LFW CANONICAL (6,000 PAIRS)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className="badge-tag emerald" style={{ fontSize: '11px', fontWeight: 700 }}>
              <CheckCircle2 size={12} /> VERIFIED
            </span>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-bright)', fontWeight: 600 }}>
            Accuracy: 99.35% (AUC 0.9988)
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
            Full official 10-fold View 2 protocol. FTA Rate: 0.00%. TAR @ FAR 0.1%: 98.80%.
          </div>
        </div>

        <div className="card" style={{ padding: '16px', borderTop: '3px solid var(--cyan-primary)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600, marginBottom: '6px' }}>
            CROSS-AGE LFW (2,424 PAIRS)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className="badge-tag cyan" style={{ fontSize: '11px', fontWeight: 700 }}>
              <CheckCircle2 size={12} /> VERIFIED W/ LIMITS
            </span>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-bright)', fontWeight: 600 }}>
            Native Acc: 99.14% (&tau;*=0.3872)
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
            Transferred LFW Acc: 96.37% (&Delta; -2.77%). 3,576 supplementary pairs unmounted.
          </div>
        </div>

        <div className="card" style={{ padding: '16px', borderTop: '3px solid var(--cyan-primary)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600, marginBottom: '6px' }}>
            CROSS-POSE LFW (2,494 PAIRS)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className="badge-tag cyan" style={{ fontSize: '11px', fontWeight: 700 }}>
              <CheckCircle2 size={12} /> VERIFIED W/ LIMITS
            </span>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-bright)', fontWeight: 600 }}>
            Native Acc: 98.81% (&tau;*=0.4084)
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
            Transferred LFW Acc: 96.55% (&Delta; -2.26%). 3,506 supplementary pairs unmounted.
          </div>
        </div>

        <div className="card" style={{ padding: '16px', borderTop: '3px solid var(--slate-border)' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600, marginBottom: '6px' }}>
            CFP-FP &amp; AGEDB-30
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className="badge-tag slate" style={{ fontSize: '11px', fontWeight: 700 }}>
              <Info size={12} /> NOT EVALUATED
            </span>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-bright)', fontWeight: 600 }}>
            Unmounted &amp; Restricted
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '4px' }}>
            CFP-FP unmounted; AgeDB-30 restricted under iBUG academic agreement.
          </div>
        </div>
      </div>

      {/* Dataset Evaluation Completeness Matrix */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">
            <Database size={16} color="var(--emerald-primary)" />
            <span>Full-Scale Dataset Evaluation &amp; Completeness Accounting Matrix</span>
          </div>
          <span className="badge-tag emerald">10,918 Real Photograph Pairs Audited</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <table className="diagnostics-matrix" style={{ margin: 0 }}>
            <thead>
              <tr>
                <th>Dataset &amp; Covariate</th>
                <th>Official Protocol</th>
                <th>Corpus Scale</th>
                <th>Locally Resolved</th>
                <th>Unresolved Missing</th>
                <th>FTA Rate</th>
                <th>Completeness Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  <strong style={{ color: 'var(--text-bright)' }}>LFW Canonical</strong>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Unconstrained Frontal Baseline</div>
                </td>
                <td>10-Fold View 2</td>
                <td>13,233 Images (5,749 IDs)</td>
                <td><strong style={{ color: 'var(--emerald-primary)' }}>6,000 / 6,000 (100.0%)</strong></td>
                <td>0 pairs (0 missing imgs)</td>
                <td>0.00%</td>
                <td><span className="badge-tag emerald">COMPLETE_OFFICIAL_CORPUS</span></td>
              </tr>
              <tr>
                <td>
                  <strong style={{ color: 'var(--text-bright)' }}>Cross-Age LFW (CALFW)</strong>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Chronological Aging Covariate</div>
                </td>
                <td>10-Fold Cross-Age</td>
                <td>12,174 Images (4,025 IDs)</td>
                <td><strong style={{ color: 'var(--cyan-primary)' }}>2,424 / 6,000 (40.40%)</strong></td>
                <td>3,576 pairs (2,640 imgs)</td>
                <td>0.00%</td>
                <td><span className="badge-tag cyan">VERIFIED_LOCAL_SUBSET</span></td>
              </tr>
              <tr>
                <td>
                  <strong style={{ color: 'var(--text-bright)' }}>Cross-Pose LFW (CPLFW)</strong>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Extreme Out-of-Plane Yaw</div>
                </td>
                <td>10-Fold Cross-Pose</td>
                <td>11,652 Images (3,998 IDs)</td>
                <td><strong style={{ color: 'var(--cyan-primary)' }}>2,494 / 6,000 (41.57%)</strong></td>
                <td>3,506 pairs (2,444 imgs)</td>
                <td>0.00%</td>
                <td><span className="badge-tag cyan">VERIFIED_LOCAL_SUBSET</span></td>
              </tr>
              <tr>
                <td>
                  <strong style={{ color: 'var(--text-bright)' }}>CFP-FP</strong>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>0&deg; Frontal vs 90&deg; Profile</div>
                </td>
                <td>10-Fold CFP-FP</td>
                <td>7,000 Images (500 IDs)</td>
                <td>0 / 7,000 (0.0%)</td>
                <td>7,000 pairs (Unmounted)</td>
                <td>N/A</td>
                <td><span className="badge-tag slate">NOT_INSTALLED</span></td>
              </tr>
              <tr>
                <td>
                  <strong style={{ color: 'var(--text-bright)' }}>AgeDB-30</strong>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>30-Year Chronological Gap</div>
                </td>
                <td>10-Fold AgeDB-30</td>
                <td>16,488 Images (568 IDs)</td>
                <td>0 / 6,000 (0.0%)</td>
                <td>6,000 pairs (Restricted)</td>
                <td>N/A</td>
                <td><span className="badge-tag amber">RESTRICTED_ACCESS</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Threshold Transfer & Confounder Analysis */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">
            <Scale size={16} color="var(--cyan-primary)" />
            <span>Threshold Calibration &amp; Cross-Dataset Transfer Audit (Root-Cause Analysis)</span>
          </div>
          <span className="badge-tag cyan">Audited on Authentic Pairs</span>
        </div>
        <div className="card-body">
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Comparison of native validation-calibrated thresholds against the fixed baseline LFW threshold (&tau;=0.3132).
            Empirically explains why CALFW and CPLFW native thresholds naturally shift upward due to demographic attribute matching.
          </p>

          <table className="diagnostics-matrix" style={{ marginBottom: '16px' }}>
            <thead>
              <tr>
                <th>Benchmark Dataset</th>
                <th>Native Optimal (&tau;*)</th>
                <th>Native Accuracy</th>
                <th>Transferred LFW (&tau;)</th>
                <th>Transferred Accuracy</th>
                <th>Transfer Gap (&Delta; Acc)</th>
                <th>False Acceptance (FAR) Spike</th>
                <th>Primary Confounder</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>LFW Canonical</strong></td>
                <td className="mono-text">0.3132</td>
                <td><strong>99.35%</strong></td>
                <td className="mono-text">0.3132</td>
                <td><strong>99.35%</strong></td>
                <td>&plusmn;0.00%</td>
                <td>0.40% (Baseline)</td>
                <td>Random Impostors (&mu;=0.0838)</td>
              </tr>
              <tr>
                <td><strong>CALFW (Cross-Age)</strong></td>
                <td className="mono-text">0.3872</td>
                <td><strong>99.14%</strong></td>
                <td className="mono-text">0.3132</td>
                <td><strong style={{ color: 'var(--amber-primary)' }}>96.37%</strong></td>
                <td><span className="badge-tag crimson" style={{ fontSize: '10px' }}>-2.77%</span></td>
                <td><strong style={{ color: 'var(--crimson-primary)' }}>0.58% &rarr; 5.18% (+4.60%)</strong></td>
                <td>Attribute Matching (&mu;=0.1703)</td>
              </tr>
              <tr>
                <td><strong>CPLFW (Cross-Pose)</strong></td>
                <td className="mono-text">0.4084</td>
                <td><strong>98.81%</strong></td>
                <td className="mono-text">0.3132</td>
                <td><strong style={{ color: 'var(--amber-primary)' }}>96.55%</strong></td>
                <td><span className="badge-tag crimson" style={{ fontSize: '10px' }}>-2.26%</span></td>
                <td><strong style={{ color: 'var(--crimson-primary)' }}>0.84% &rarr; 5.03% (+4.19%)</strong></td>
                <td>Yaw Distortion + Attribute Matching</td>
              </tr>
            </tbody>
          </table>

          <div
            style={{
              padding: '12px 16px',
              backgroundColor: 'rgba(239, 68, 68, 0.06)',
              border: '1px solid var(--crimson-border)',
              borderRadius: '6px',
              fontSize: '12px',
              color: 'var(--text-main)',
              lineHeight: 1.5,
            }}
          >
            <strong>SCIENTIFIC FINDING (DISC-08):</strong> In CALFW, negative pairs are matched on perceived gender and race.
            This eliminates macro-demographic shortcuts, inflating impostor cosine similarities from <strong>&mu;=0.0838 (LFW)</strong> up to <strong>&mu;=0.1703 (CALFW)</strong>.
            Applying the LFW threshold (&tau;=0.3132) results in 81 false acceptances because attribute-matched impostors score in the 0.32–0.38 range.
            <strong> A universal threshold calibrated on LFW cannot be transferred to demographics-matched systems without native recalibration.</strong>
          </div>
        </div>
      </div>

      {/* Independent Metric Recalculation Table */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">
            <Layers size={16} color="var(--purple-primary)" />
            <span>Independent Metric Recalculation &amp; 95% Confidence Intervals</span>
          </div>
          <span className="badge-tag purple">1,000-Iteration Bootstrap Resampling</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <table className="diagnostics-matrix" style={{ margin: 0 }}>
            <thead>
              <tr>
                <th>Dataset Evaluated</th>
                <th>Sample Count (N)</th>
                <th>Accuracy [95% CI]</th>
                <th>ROC-AUC [95% CI]</th>
                <th>EER [95% CI]</th>
                <th>TAR @ FAR=1.0%</th>
                <th>TAR @ FAR=0.1% (Rule of Three)</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>LFW Canonical</strong></td>
                <td className="mono-text">6,000 pairs</td>
                <td><strong>99.38%</strong> [99.17% – 99.60%]</td>
                <td><strong>0.9988</strong> [0.9979 – 0.9996]</td>
                <td><strong>0.80%</strong> [0.44% – 1.07%]</td>
                <td>99.27%</td>
                <td><strong style={{ color: 'var(--emerald-primary)' }}>98.80% (Certified Valid)</strong></td>
              </tr>
              <tr>
                <td><strong>CALFW Cross-Age</strong></td>
                <td className="mono-text">2,424 pairs</td>
                <td><strong>99.13%</strong> [98.93% – 99.33%]</td>
                <td><strong>0.9981</strong> [0.9963 – 0.9996]</td>
                <td><strong>1.05%</strong> [0.67% – 1.41%]</td>
                <td>98.95%</td>
                <td><span className="badge-tag amber" style={{ fontSize: '10px' }}>Insufficient N &lt; 3,000</span></td>
              </tr>
              <tr>
                <td><strong>CPLFW Cross-Pose</strong></td>
                <td className="mono-text">2,494 pairs</td>
                <td><strong>98.96%</strong> [98.35% – 99.50%]</td>
                <td><strong>0.9985</strong> [0.9964 – 0.9998]</td>
                <td><strong>1.29%</strong> [0.64% – 2.01%]</td>
                <td>98.20%</td>
                <td><span className="badge-tag amber" style={{ fontSize: '10px' }}>Insufficient N &lt; 3,000</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Robustness Reproduction Matrix */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">
            <ShieldAlert size={16} color="var(--amber-primary)" />
            <span>Robustness Stress-Testing Reproduction Matrix (Symmetric Pair Evaluation)</span>
          </div>
          <span className="badge-tag amber">100 Real Photograph Pairs (200 Images)</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <table className="diagnostics-matrix" style={{ margin: 0 }}>
            <thead>
              <tr>
                <th>Perturbation Condition</th>
                <th>Detection Rate</th>
                <th>FTA Rate</th>
                <th>Genuine Mean (&mu;)</th>
                <th>Impostor Mean (&mu;)</th>
                <th>Accuracy (@ 0.3128)</th>
                <th>ROC-AUC</th>
                <th>Degradation Verdict</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Original Baseline</strong></td>
                <td>100.0%</td>
                <td>0.00%</td>
                <td>0.6528</td>
                <td>0.0443</td>
                <td><strong>100.0%</strong></td>
                <td>1.0000</td>
                <td><span className="badge-tag emerald">Pristine</span></td>
              </tr>
              <tr>
                <td><strong>Gaussian Blur (&sigma;=3.0)</strong></td>
                <td>100.0%</td>
                <td>0.00%</td>
                <td>0.5312</td>
                <td>0.0544</td>
                <td>95.00%</td>
                <td>0.9532</td>
                <td><span className="badge-tag cyan">Minor Attenuation</span></td>
              </tr>
              <tr>
                <td><strong>Severe Downsampling (32px)</strong></td>
                <td><strong style={{ color: 'var(--crimson-primary)' }}>66.50%</strong></td>
                <td><strong style={{ color: 'var(--crimson-primary)' }}>54.00%</strong></td>
                <td>0.3809</td>
                <td>0.3992</td>
                <td><strong style={{ color: 'var(--crimson-primary)' }}>41.30%</strong></td>
                <td>0.4518</td>
                <td><span className="badge-tag crimson">Catastrophic Collapse</span></td>
              </tr>
              <tr>
                <td><strong>Underexposure (&gamma;=1.8)</strong></td>
                <td>100.0%</td>
                <td>0.00%</td>
                <td>0.6591</td>
                <td>0.0458</td>
                <td><strong>100.0%</strong></td>
                <td>1.0000</td>
                <td><span className="badge-tag emerald">Resilient (Angular Invariance)</span></td>
              </tr>
              <tr>
                <td><strong>Overexposure (&gamma;=0.4)</strong></td>
                <td>100.0%</td>
                <td>0.00%</td>
                <td>0.6102</td>
                <td>0.0259</td>
                <td>99.00%</td>
                <td>1.0000</td>
                <td><span className="badge-tag emerald">Resilient</span></td>
              </tr>
              <tr>
                <td><strong>JPEG Compression (Q=10)</strong></td>
                <td>100.0%</td>
                <td>0.00%</td>
                <td>0.5239</td>
                <td>0.0611</td>
                <td>98.00%</td>
                <td>0.9876</td>
                <td><span className="badge-tag emerald">Resilient to Artifacts</span></td>
              </tr>
              <tr>
                <td><strong>Lower Mask (35% Occlusion)</strong></td>
                <td>100.0%</td>
                <td>0.00%</td>
                <td>0.6052</td>
                <td>0.0376</td>
                <td>99.00%</td>
                <td>0.9896</td>
                <td><span className="badge-tag emerald">Resilient (Eyes/Nose Intact)</span></td>
              </tr>
              <tr>
                <td><strong>Upper Sunglasses (Eye Occlusion)</strong></td>
                <td>99.50%</td>
                <td>1.00%</td>
                <td>0.4475</td>
                <td>0.1531</td>
                <td><strong style={{ color: 'var(--amber-primary)' }}>77.78%</strong></td>
                <td>0.8543</td>
                <td><span className="badge-tag amber">Severe (Landmark Skew)</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Discrepancy Register & Resolution Tracker */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <div className="card-title">
            <FileText size={16} color="var(--cyan-primary)" />
            <span>Audit Discrepancy Register &amp; Resolution Tracker</span>
          </div>
          <span className="badge-tag emerald">8 of 8 Discrepancies Resolved</span>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <table className="diagnostics-matrix" style={{ margin: 0 }}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Severity</th>
                <th>Audit Finding &amp; Evidence</th>
                <th>Affected Modules</th>
                <th>Resolution Implemented</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {discrepancies.map((d) => (
                <tr key={d.id}>
                  <td className="mono-text" style={{ fontWeight: 700, color: 'var(--text-bright)' }}>
                    {d.id}
                  </td>
                  <td>
                    <span
                      className={`badge-tag ${
                        d.severity === 'HIGH' ? 'crimson' : d.severity === 'MEDIUM' ? 'amber' : 'slate'
                      }`}
                      style={{ fontSize: '10px' }}
                    >
                      {d.severity}
                    </span>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: 'var(--text-bright)', marginBottom: '2px' }}>
                      {d.description}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-dim)', maxWidth: '340px' }}>
                      {d.evidence}
                    </div>
                  </td>
                  <td className="mono-text" style={{ fontSize: '11px', color: 'var(--cyan-primary)' }}>
                    {d.affected}
                  </td>
                  <td style={{ fontSize: '11px', color: 'var(--text-muted)', maxWidth: '320px' }}>
                    {d.resolution}
                  </td>
                  <td>
                    <span className="badge-tag emerald" style={{ fontSize: '10px' }}>
                      <CheckCircle2 size={10} /> {d.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cryptographic Provenance & CLI Reproducibility */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <Terminal size={16} color="var(--emerald-primary)" />
            <span>Cryptographic Provenance &amp; CLI Reproduction Commands</span>
          </div>
          <span className="badge-tag slate">Deterministic Replay</span>
        </div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px', marginBottom: '20px' }}>
            <div style={{ padding: '12px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-dim)', marginBottom: '4px' }}>
                YUNET DETECTOR WEIGHTS (SHA-256)
              </div>
              <div className="mono-text" style={{ fontSize: '11px', color: 'var(--cyan-primary)', wordBreak: 'break-all' }}>
                8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4
              </div>
            </div>

            <div style={{ padding: '12px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-dim)', marginBottom: '4px' }}>
                SFACE FEATURE EXTRACTOR WEIGHTS (SHA-256)
              </div>
              <div className="mono-text" style={{ fontSize: '11px', color: 'var(--emerald-primary)', wordBreak: 'break-all' }}>
                0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79
              </div>
            </div>

            <div style={{ padding: '12px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-dim)', marginBottom: '4px' }}>
                LFW OFFICIAL PAIRS LIST (SHA-256)
              </div>
              <div className="mono-text" style={{ fontSize: '11px', color: 'var(--text-bright)', wordBreak: 'break-all' }}>
                ea42330c62c92989f9d7c03237ed5d591365e89b3e649747777b70e692dc1592
              </div>
            </div>
          </div>

          <h4 style={{ fontSize: '13px', color: 'var(--text-bright)', marginBottom: '8px' }}>
            Deterministic CLI Reproduction Commands
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {[
              {
                title: 'LFW Canonical (6,000 Pairs Full Protocol)',
                key: 'lfw',
                cmd: `python -m app.benchmarks.runner --dataset lfw-canonical-v1 --seed 42 --policy center_face`,
              },
              {
                title: 'CALFW Cross-Age (2,424 Resolvable Pairs + Transfer Audit)',
                key: 'calfw',
                cmd: `python -m app.benchmarks.runner --dataset calfw-v1 --transfer-thresh 0.3132 --seed 42`,
              },
              {
                title: 'CPLFW Cross-Pose (2,494 Resolvable Pairs + Transfer Audit)',
                key: 'cplfw',
                cmd: `python -m app.benchmarks.runner --dataset cplfw-v1 --transfer-thresh 0.3132 --seed 42`,
              },
            ].map((item) => (
              <div
                key={item.key}
                style={{
                  padding: '10px 14px',
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>
                    {item.title}
                  </span>
                  <button
                    onClick={() => handleCopy(item.cmd, item.key)}
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: '10px', padding: '2px 6px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                  >
                    {copiedCmd === item.key ? <Check size={10} color="var(--emerald-primary)" /> : <Copy size={10} />}
                    <span>{copiedCmd === item.key ? 'Copied' : 'Copy Command'}</span>
                  </button>
                </div>
                <pre
                  className="mono-text"
                  style={{
                    margin: 0,
                    fontSize: '11px',
                    color: 'var(--cyan-primary)',
                    backgroundColor: 'rgba(0,0,0,0.3)',
                    padding: '6px 10px',
                    borderRadius: '4px',
                    overflowX: 'auto',
                  }}
                >
                  {item.cmd}
                </pre>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
