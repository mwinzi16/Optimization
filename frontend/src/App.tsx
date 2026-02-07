import React, { useEffect } from 'react';
import { useUiStore } from './stores/uiStore';
import { useDataStore } from './stores/dataStore';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ToastProvider } from './components/Toast';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { TabNavigation } from './components/TabNavigation';
import { DistributionTab } from './components/DistributionTab';
import { AllocationTab } from './components/AllocationTab';
import { RiskAnalysisTab } from './components/RiskAnalysisTab';
import { StatsTab } from './components/StatsTab';

const TAB_COMPONENTS: Record<string, React.FC> = {
  distribution: DistributionTab,
  allocation: AllocationTab,
  risk: RiskAnalysisTab,
  stats: StatsTab,
};

export default function App() {
  const { activeTab, checkHealth } = useUiStore();
  const { fetchAssets } = useDataStore();

  useEffect(() => {
    checkHealth();
    fetchAssets();
    const interval = setInterval(checkHealth, 30_000);
    return () => clearInterval(interval);
  }, [checkHealth, fetchAssets]);

  const ActivePanel = TAB_COMPONENTS[activeTab] ?? DistributionTab;

  return (
    <ErrorBoundary>
      <ToastProvider>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
            <Header />
            <TabNavigation />
            <div className="flex-1 overflow-y-auto p-4 lg:p-6">
              <ActivePanel />
            </div>
          </main>
        </div>
      </ToastProvider>
    </ErrorBoundary>
  );
}
