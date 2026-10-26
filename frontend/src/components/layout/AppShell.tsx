import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ToastContainer, type ToastMessage } from '../common/Toast';
import type { NavTab, HealthResponse, EngineMetadata } from '../../types';

interface AppShellProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  health: HealthResponse | null;
  engineInfo: EngineMetadata | null;
  isBackendOnline: boolean;
  historyCount: number;
  onOpenHistory: () => void;
  toasts: ToastMessage[];
  onDismissToast: (id: string) => void;
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({
  activeTab,
  onSelectTab,
  health,
  engineInfo,
  isBackendOnline,
  historyCount,
  onOpenHistory,
  toasts,
  onDismissToast,
  children,
}) => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="app-container">
      {/* Cybernetic ambient grid overlay */}
      <div className="ambient-grid" />

      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={(tab) => {
          onSelectTab(tab);
          setMobileOpen(false);
        }}
        health={health}
        isBackendOnline={isBackendOnline}
        mobileOpen={mobileOpen}
      />

      {/* Main Content Area */}
      <div className="main-wrapper">
        <Header
          activeTab={activeTab}
          engineInfo={engineInfo}
          historyCount={historyCount}
          onOpenHistory={onOpenHistory}
          onToggleMobileNav={() => setMobileOpen(!mobileOpen)}
        />

        <main className="content-viewport" id="main-content">
          {children}
        </main>
      </div>

      {/* Global Toast Container */}
      <ToastContainer toasts={toasts} onDismiss={onDismissToast} />
    </div>
  );
};
