import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { DashboardView } from '../components/dashboard/DashboardView';
import * as api from '../services/api';
import type { DashboardStatsResponse, ReadinessResponse, ComparisonHistoryRecord } from '../types';

describe('DashboardView Component (Step 10 Production Telemetry)', () => {
  const mockStats: DashboardStatsResponse = {
    total_comparisons: 42,
    successful_matches: 28,
    successful_non_matches: 14,
    failed_comparisons: 0,
    average_latency_ms: 24.5,
    total_fta_events: 1,
    fta_rate_percent: 2.38,
    fta_breakdown: { no_face_detected: 1 },
    database_size_bytes: 40960,
    schema_version: 1,
  };

  const mockReadiness: ReadinessResponse = {
    ready: true,
    status: 'ready',
    models_loaded: true,
    database_connected: true,
    active_threshold_profile: 'balanced',
    timestamp: '2026-11-02T10:00:00Z',
  };

  const mockHistory: ComparisonHistoryRecord[] = [
    {
      id: 'audit-001',
      timestamp: '2026-11-02T10:05:00Z',
      probe_hash_prefix: '7a1b2c3d',
      reference_hash_prefix: '8e9f0a1b',
      similarity_score: 0.7421,
      threshold_profile: 'high_security',
      threshold_used: 0.3600,
      decision: 'MATCH',
      inference_latency_ms: 22.8,
      has_quality_warnings: false,
      status: 'SUCCESS',
    },
    {
      id: 'audit-002',
      timestamp: '2026-11-02T10:06:00Z',
      probe_hash_prefix: '3f4a5b6c',
      reference_hash_prefix: '1d2e3f4a',
      similarity_score: 0.1850,
      threshold_profile: 'balanced',
      threshold_used: 0.3132,
      decision: 'NO_MATCH',
      inference_latency_ms: 25.1,
      has_quality_warnings: true,
      status: 'SUCCESS',
    },
  ];

  beforeEach(() => {
    vi.spyOn(api, 'fetchDashboardStats').mockResolvedValue(mockStats);
    vi.spyOn(api, 'fetchReadiness').mockResolvedValue(mockReadiness);
    vi.spyOn(api, 'fetchComparisonHistory').mockResolvedValue(mockHistory);
  });

  it('renders dashboard header and readiness telemetry', async () => {
    render(<DashboardView onNavigate={vi.fn()} onShowToast={vi.fn()} />);

    expect(screen.getByText(/Production Biometric Audit Dashboard/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/YuNet \+ SFace \(CPU INT8\/FP32\)/i)).toBeInTheDocument();
      expect(screen.getByText(/SQLite \(WAL Mode, Schema v1\)/i)).toBeInTheDocument();
      expect(screen.getByText(/100% Ephemeral RAM Only/i)).toBeInTheDocument();
    });
  });

  it('displays accurate metric cards loaded from SQLite', async () => {
    render(<DashboardView onNavigate={vi.fn()} onShowToast={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText('28')).toBeInTheDocument();
      expect(screen.getByText('14')).toBeInTheDocument();
      expect(screen.getByText('24.5')).toBeInTheDocument();
      expect(screen.getByText('2.38%')).toBeInTheDocument();
    });
  });

  it('renders cryptographic audit trail table with SHA-256 prefixes and decision badges', async () => {
    render(<DashboardView onNavigate={vi.fn()} onShowToast={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText('7a1b2c3d')).toBeInTheDocument();
      expect(screen.getByText('8e9f0a1b')).toBeInTheDocument();
      expect(screen.getByText('+0.7421')).toBeInTheDocument();
      expect(screen.getByText('+0.1850')).toBeInTheDocument();
      expect(screen.getByText('Quality Flag')).toBeInTheDocument();
    });
  });

  it('renders Step 10 operating profiles with exact thresholds', async () => {
    render(<DashboardView onNavigate={vi.fn()} onShowToast={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/High Security Profile/i)).toBeInTheDocument();
      expect(screen.getByText(/Balanced Profile \(LFW Native\)/i)).toBeInTheDocument();
      expect(screen.getByText(/High Convenience Profile/i)).toBeInTheDocument();
      expect(screen.getByText(/τ = 0.3600/i)).toBeInTheDocument();
      expect(screen.getByText(/τ = 0.3132/i)).toBeInTheDocument();
      expect(screen.getByText(/τ = 0.2500/i)).toBeInTheDocument();
    });
  });
});

