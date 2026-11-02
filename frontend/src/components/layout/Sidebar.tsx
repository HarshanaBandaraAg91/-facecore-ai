import React from 'react';
import {
  Activity,
  ScanFace,
  FlaskConical,
  BarChart3,
  Settings,
  ShieldCheck,
  Cpu,
} from 'lucide-react';
import type { NavTab, HealthResponse } from '../../types';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  health: HealthResponse | null;
  isBackendOnline: boolean;
  mobileOpen: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  health,
  isBackendOnline,
  mobileOpen,
}) => {
  const navItems = [
    { id: 'dashboard' as NavTab, label: 'Audit Dashboard', icon: Activity },
    { id: 'compare' as NavTab, label: 'Face Comparison', icon: ScanFace },
    { id: 'testlab' as NavTab, label: 'Test Lab', icon: FlaskConical },
    { id: 'benchmarks' as NavTab, label: 'Model Benchmarks', icon: BarChart3 },
    { id: 'settings' as NavTab, label: 'Settings & Privacy', icon: Settings },
  ];

  return (
    <aside className={`app-sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="sidebar-brand">
        <div className="brand-icon-box">
          <ScanFace size={22} />
        </div>
        <div className="brand-text">
          <h1>FACECORE AI</h1>
          <span>BIOMETRIC LAB // V0.1</span>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Main Navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`nav-item-btn ${isActive ? 'active' : ''}`}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="system-status-indicator">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              className={`status-dot ${isBackendOnline ? 'online' : 'offline'}`}
            />
            <span style={{ color: 'var(--text-bright)', fontSize: '11px' }}>
              {isBackendOnline ? 'API Connected' : 'API Offline'}
            </span>
          </div>
          <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
            {health?.version || 'v0.1.0'}
          </span>
        </div>

        <div
          style={{
            padding: '10px',
            backgroundColor: 'var(--bg-input)',
            borderRadius: '6px',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              color: 'var(--emerald-primary)',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
            }}
          >
            <ShieldCheck size={14} />
            <span>EPHEMERAL PRIVACY</span>
          </div>
          <p style={{ color: 'var(--text-dim)', fontSize: '10px', lineHeight: '1.3' }}>
            In-memory execution only. Zero biometric data saved to disk or network.
          </p>
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            color: 'var(--text-muted)',
            fontSize: '10px',
            fontFamily: 'var(--font-mono)',
            padding: '2px 4px',
          }}
        >
          <Cpu size={12} />
          <span>ENGINE: MODULAR STUB</span>
        </div>
      </div>
    </aside>
  );
};
