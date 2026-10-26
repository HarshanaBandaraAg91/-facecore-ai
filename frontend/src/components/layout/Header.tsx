import React from 'react';
import {
  Menu,
  History,
  Activity,
  Layers,
  ShieldAlert,
} from 'lucide-react';
import type { NavTab, EngineMetadata } from '../../types';

interface HeaderProps {
  activeTab: NavTab;
  engineInfo: EngineMetadata | null;
  historyCount: number;
  onOpenHistory: () => void;
  onToggleMobileNav: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  engineInfo,
  historyCount,
  onOpenHistory,
  onToggleMobileNav,
}) => {
  const getTabTitle = (tab: NavTab) => {
    switch (tab) {
      case 'compare':
        return 'Facial Image Comparison & Quality Validation';
      case 'testlab':
        return 'Batch Evaluation & Testing Laboratory';
      case 'benchmarks':
        return 'Standardized Model Benchmarks (LFW / CFP-FP / AgeDB)';
      case 'settings':
        return 'Platform Settings & Privacy Architecture';
      default:
        return 'FACECORE AI';
    }
  };

  return (
    <header className="top-header">
      <div className="header-meta">
        <button
          className="btn btn-secondary btn-sm"
          onClick={onToggleMobileNav}
          style={{ display: 'none' }}
          id="mobile-nav-toggle"
          aria-label="Toggle navigation"
        >
          <Menu size={16} />
        </button>

        <div className="header-title-badge">
          <Layers size={16} color="var(--crimson-primary)" />
          <span style={{ color: 'var(--text-bright)' }}>{getTabTitle(activeTab)}</span>
        </div>
      </div>

      <div className="header-actions">
        {/* Engine status indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--bg-input)',
            border: '1px solid var(--border-subtle)',
            padding: '4px 10px',
            borderRadius: '6px',
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
          }}
        >
          <Activity size={12} color="var(--amber-primary)" />
          <span style={{ color: 'var(--text-muted)' }}>ENGINE:</span>
          <span style={{ color: 'var(--amber-primary)', fontWeight: 600 }}>
            {engineInfo?.status === 'pending_integration'
              ? 'STEP 01 MODULAR BASELINE'
              : engineInfo?.name || 'INITIALIZING'}
          </span>
        </div>

        {/* History drawer trigger */}
        <button
          onClick={onOpenHistory}
          className="btn btn-secondary btn-sm"
          title="Inspect session comparison history (metadata only)"
        >
          <History size={15} />
          <span>Session Log</span>
          {historyCount > 0 && (
            <span
              style={{
                backgroundColor: 'var(--crimson-primary)',
                color: '#fff',
                fontSize: '10px',
                fontWeight: 700,
                borderRadius: '10px',
                padding: '1px 6px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              {historyCount}
            </span>
          )}
        </button>

        {/* Cautious interpretation reminder badge */}
        <div
          className="badge-tag amber"
          style={{ cursor: 'help' }}
          title="FACECORE AI enforces scientific integrity: Similarity scores reflect feature proximity, never 100% identity proof."
        >
          <ShieldAlert size={12} />
          <span>PROBABILISTIC ANALYSIS ONLY</span>
        </div>
      </div>
    </header>
  );
};
