import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import App from '../App';

describe('FACECORE AI Frontend Interface', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // Default fetch mock returning health and engine metadata
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/health')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              status: 'ok',
              app: 'FACECORE AI',
              version: '0.1.0-alpha',
              timestamp: '2026-10-26T21:00:00Z',
              engine_status: 'pending_integration',
              security_mode: 'ephemeral_local_strict',
            }),
        });
      }
      if (url.includes('/api/engine-info')) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              engine_id: 'stub-modular-v1',
              name: 'Modular Stub Interface',
              version: '0.1.0-alpha',
              status: 'pending_integration',
              is_mock_data: false,
              description: 'Modular stub awaiting embedding model.',
              supported_models: ['ArcFace', 'AdaFace'],
            }),
        });
      }
      return Promise.reject(new Error(`Unhandled mock url: ${url}`));
    });
  });

  it('renders application branding and header elements', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/FACECORE AI/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/BIOMETRIC LAB \/\/ V0.1/i)).toBeInTheDocument();
  });

  it('renders dual image upload panels for Probe (Image A) and Reference (Image B)', async () => {
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/IMAGE A \(PROBE \/ QUERY\)/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/IMAGE B \(REFERENCE \/ GALLERY\)/i)).toBeInTheDocument();
  });

  it('keeps Compare button disabled when slots are empty', async () => {
    render(<App />);
    await waitFor(() => {
      const compareBtn = screen.getByRole('button', { name: /compare facial images/i });
      expect(compareBtn).toBeDisabled();
    });
  });

  it('navigates to Test Lab page and displays batch test architecture', async () => {
    render(<App />);
    const testLabBtn = screen.getByRole('button', { name: /test lab/i });
    fireEvent.click(testLabBtn);

    await waitFor(() => {
      expect(screen.getByText(/Test Lab & Batch Evaluation Suite/i)).toBeInTheDocument();
      expect(screen.getByText(/Execution Suspended for Phase 1/i)).toBeInTheDocument();
    });
  });

  it('navigates to Model Benchmarks and displays anti-fabrication statement', async () => {
    render(<App />);
    const benchBtn = screen.getByRole('button', { name: /model benchmarks/i });
    fireEvent.click(benchBtn);

    await waitFor(() => {
      expect(screen.getAllByText(/Standardized Model Benchmarks/i).length).toBeGreaterThan(0);
      expect(screen.getByText(/NO BENCHMARKS EXECUTED YET/i)).toBeInTheDocument();
    });
  });

  it('navigates to Settings & Privacy page and displays local privacy guarantees', async () => {
    render(<App />);
    const settingsBtn = screen.getByRole('button', { name: /settings & privacy/i });
    fireEvent.click(settingsBtn);

    await waitFor(() => {
      expect(
        screen.getAllByText(/Platform Settings & Privacy Architecture/i).length
      ).toBeGreaterThan(0);
      expect(
        screen.getByText(/100% In-Memory Ephemeral Execution/i)
      ).toBeInTheDocument();
    });
  });

  it('updates theme attribute when theme selection changes', async () => {
    render(<App />);
    const settingsBtn = screen.getByRole('button', { name: /settings & privacy/i });
    fireEvent.click(settingsBtn);

    await waitFor(() => {
      expect(screen.getByLabelText(/Tactical Charcoal/i)).toBeInTheDocument();
    });

    const charcoalRadio = screen.getByLabelText(/Tactical Charcoal/i);
    fireEvent.click(charcoalRadio);

    await waitFor(() => {
      expect(document.documentElement.getAttribute('data-theme')).toBe(
        'tactical-charcoal'
      );
    });
  });
});
