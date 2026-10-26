import { useState, useEffect, useCallback } from 'react';
import { AppShell } from './components/layout/AppShell';
import { ComparisonWorkspace } from './components/comparison/ComparisonWorkspace';
import { HistoryDrawer } from './components/comparison/HistoryDrawer';
import { TestLabView } from './components/testlab/TestLabView';
import { BenchmarksView } from './components/benchmarks/BenchmarksView';
import { SettingsView } from './components/settings/SettingsView';
import type { ToastMessage } from './components/common/Toast';
import type {
  NavTab,
  Theme,
  HealthResponse,
  EngineMetadata,
  ComparisonHistoryEntry,
} from './types';
import { fetchHealth, fetchEngineInfo } from './services/api';

export function App() {
  const [activeTab, setActiveTab] = useState<NavTab>('compare');
  const [theme, setTheme] = useState<Theme>('cyber-dark');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [engineInfo, setEngineInfo] = useState<EngineMetadata | null>(null);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(false);
  const [history, setHistory] = useState<ComparisonHistoryEntry[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState<boolean>(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Apply theme to document element
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Toast dispatcher
  const showToast = useCallback(
    (msg: {
      type: 'success' | 'error' | 'info' | 'warning';
      message: string;
      title?: string;
    }) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`;
      const newToast: ToastMessage = { id, ...msg };
      setToasts((prev) => [...prev, newToast]);

      // Auto dismiss after 6 seconds
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 6000);
    },
    []
  );

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // Fetch initial health and engine info
  const loadSystemStatus = useCallback(async () => {
    try {
      const [h, e] = await Promise.all([fetchHealth(), fetchEngineInfo()]);
      setHealth(h);
      setEngineInfo(e);
      setIsBackendOnline(true);
    } catch {
      setIsBackendOnline(false);
      // We don't spam toast on initial load if backend isn't started yet
    }
  }, []);

  useEffect(() => {
    loadSystemStatus();
    // Heartbeat every 30 seconds
    const interval = setInterval(loadSystemStatus, 30000);
    return () => clearInterval(interval);
  }, [loadSystemStatus]);

  // Add history record (metadata only)
  const handleAddHistory = (entry: ComparisonHistoryEntry) => {
    setHistory((prev) => [entry, ...prev.slice(0, 49)]); // Cap at 50 in memory
  };

  const handleClearHistory = () => {
    setHistory([]);
    showToast({
      type: 'info',
      message: 'Session evaluation history cleared.',
    });
  };

  return (
    <AppShell
      activeTab={activeTab}
      onSelectTab={setActiveTab}
      health={health}
      engineInfo={engineInfo}
      isBackendOnline={isBackendOnline}
      historyCount={history.length}
      onOpenHistory={() => setIsHistoryOpen(true)}
      toasts={toasts}
      onDismissToast={dismissToast}
    >
      {activeTab === 'compare' && (
        <ComparisonWorkspace
          onAddHistory={handleAddHistory}
          onShowToast={showToast}
        />
      )}

      {activeTab === 'testlab' && <TestLabView />}

      {activeTab === 'benchmarks' && <BenchmarksView />}

      {activeTab === 'settings' && (
        <SettingsView
          currentTheme={theme}
          onSelectTheme={setTheme}
          health={health}
          onRefreshHealth={loadSystemStatus}
          onShowToast={showToast}
        />
      )}

      {/* Metadata History Drawer */}
      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={history}
        onClearHistory={handleClearHistory}
      />
    </AppShell>
  );
}

export default App;
