import { useState, useEffect, useCallback } from 'react';
import { TrendingUp, BarChart3, PieChart, AlertTriangle, FileText, Zap, Menu, X } from 'lucide-react';
import { OptimizationResponse, OptimizationMethod, TabType, AssetInfo, EfficientFrontierPoint } from './types';
import { optimizePortfolio, fetchAssets, fetchEfficientFrontier, checkHealth, uploadData, resetData } from './api';
import Sidebar from './components/Sidebar';
import MetricCard from './components/MetricCard';
import DistributionTab from './components/DistributionTab';
import AllocationTab from './components/AllocationTab';
import RiskAnalysisTab from './components/RiskAnalysisTab';
import StatsTab from './components/StatsTab';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider, useToast } from './components/Toast';
import { PageSkeleton } from './components/Skeleton';
import { METRIC_TOOLTIPS } from './components/Tooltip';
import { useKeyboardShortcut, useMediaQuery } from './hooks';

interface DataInfo {
  n_assets: number;
  n_scenarios: number;
  asset_names: string[];
  isCustom: boolean;
}

function AppContent() {
  const toast = useToast();
  const isMobile = useMediaQuery('(max-width: 768px)');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  // State
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('distribution');
  const [dataInfo, setDataInfo] = useState<DataInfo | null>(null);
  
  // Optimization parameters
  const [method, setMethod] = useState<OptimizationMethod>('Maximum Sharpe Ratio');
  const [minWeight, setMinWeight] = useState(0);
  const [maxWeight, setMaxWeight] = useState(100);
  const [riskFreeRate, setRiskFreeRate] = useState(0); // Risk-free rate embedded in returns
  const [cvarAlpha, setCvarAlpha] = useState(95);
  const [riskAversion, setRiskAversion] = useState(1.0);
  const [expRiskAversion, setExpRiskAversion] = useState(0.5);
  const [constraintType, setConstraintType] = useState<'volatility' | 'cvar'>('volatility');
  const [maxVolatility, setMaxVolatility] = useState(15);
  const [maxCvar, setMaxCvar] = useState(25);
  const [cvarConstraintAlpha, setCvarConstraintAlpha] = useState(95);
  
  // Results
  const [result, setResult] = useState<OptimizationResponse | null>(null);
  const [assets, setAssets] = useState<AssetInfo[]>([]);
  const [frontier, setFrontier] = useState<EfficientFrontierPoint[]>([]);

  // Check API health on mount
  useEffect(() => {
    const checkApi = async () => {
      const healthy = await checkHealth();
      setIsConnected(healthy);
      if (healthy) {
        const assetData = await fetchAssets();
        setAssets(assetData);
        setDataInfo({
          n_assets: assetData.length,
          n_scenarios: 10000, // Default sample data
          asset_names: assetData.map(a => a.name),
          isCustom: false
        });
      }
    };
    checkApi();
  }, []);

  // Handle file upload
  const handleUpload = useCallback(async (file: File) => {
    setIsUploading(true);
    setError(null);
    try {
      const response = await uploadData(file);
      setDataInfo({
        n_assets: response.n_assets,
        n_scenarios: response.n_scenarios,
        asset_names: response.asset_names,
        isCustom: true
      });
      // Refresh assets and rerun optimization
      const assetData = await fetchAssets();
      setAssets(assetData);
      setResult(null); // Clear result to trigger rerun
      toast.success(`Loaded ${response.n_assets} assets with ${response.n_scenarios.toLocaleString()} scenarios`);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      setError(message);
      toast.error(message);
    } finally {
      setIsUploading(false);
    }
  }, [toast]);

  // Handle reset to sample data
  const handleResetData = useCallback(async () => {
    try {
      await resetData();
      const assetData = await fetchAssets();
      setAssets(assetData);
      setDataInfo({
        n_assets: assetData.length,
        n_scenarios: 10000,
        asset_names: assetData.map(a => a.name),
        isCustom: false
      });
      setResult(null); // Clear result to trigger rerun
      toast.success('Reset to sample data');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Reset failed';
      setError(message);
      toast.error(message);
    }
  }, [toast]);

  // Run optimization
  const runOptimization = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await optimizePortfolio({
        method,
        min_weight: minWeight / 100,
        max_weight: maxWeight / 100,
        risk_free_rate: riskFreeRate / 100,
        cvar_alpha: (100 - cvarAlpha) / 100,
        risk_aversion: riskAversion,
        exp_risk_aversion: expRiskAversion,
        max_volatility: maxVolatility / 100,
        max_cvar: maxCvar / 100,
        constraint_type: constraintType,
        cvar_constraint_alpha: (100 - cvarConstraintAlpha) / 100,
      });
      
      setResult(response);
      
      // Also fetch efficient frontier with same risk-free rate
      const frontierData = await fetchEfficientFrontier(minWeight / 100, maxWeight / 100, 20, riskFreeRate / 100);
      setFrontier(frontierData);
      
      if (response.status === 'optimal') {
        toast.success('Optimization complete');
      } else {
        toast.warning('Optimization completed with fallback solution');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Optimization failed';
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  }, [method, minWeight, maxWeight, riskFreeRate, cvarAlpha, riskAversion, expRiskAversion, constraintType, maxVolatility, maxCvar, cvarConstraintAlpha, toast]);

  // Keyboard shortcuts
  useKeyboardShortcut('r', runOptimization, { ctrl: true });
  useKeyboardShortcut('Escape', () => setIsSidebarOpen(false));
  
  // Close sidebar on mobile when changing tabs
  const handleTabChange = useCallback((tab: TabType) => {
    setActiveTab(tab);
    if (isMobile) setIsSidebarOpen(false);
  }, [isMobile]);

  // Auto-run on first load when connected
  useEffect(() => {
    if (isConnected && !result) {
      runOptimization();
    }
  }, [isConnected, result, runOptimization]);

  const tabs = [
    { id: 'distribution' as TabType, label: 'Distribution', icon: BarChart3 },
    { id: 'allocation' as TabType, label: 'Allocation', icon: PieChart },
    { id: 'risk' as TabType, label: 'Risk Analysis', icon: AlertTriangle },
    { id: 'stats' as TabType, label: 'Statistics', icon: FileText },
  ];

  if (!isConnected) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #0a0a0b 0%, #111113 100%)' }}>
        <div className="card p-10 text-center max-w-md" role="alert" aria-live="polite">
          <div className="spinner mx-auto mb-6" aria-label="Loading"></div>
          <h2 className="text-xl font-semibold text-white mb-3">Connecting to API...</h2>
          <p className="text-gray-400">Ensure the backend server is running on port 8000</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex" style={{ background: 'linear-gradient(135deg, #0a0a0b 0%, #0d1117 100%)' }}>
      {/* Skip link for accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      
      {/* Mobile sidebar overlay */}
      {isMobile && (
        <div 
          className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`}
          onClick={() => setIsSidebarOpen(false)}
          aria-hidden="true"
        />
      )}
      
      {/* Sidebar */}
      <div className={`${isMobile ? 'sidebar-responsive' : ''} ${isSidebarOpen ? 'open' : ''}`}>
        <Sidebar
          method={method}
          setMethod={setMethod}
          minWeight={minWeight}
          setMinWeight={setMinWeight}
          maxWeight={maxWeight}
          setMaxWeight={setMaxWeight}
          riskFreeRate={riskFreeRate}
          setRiskFreeRate={setRiskFreeRate}
          cvarAlpha={cvarAlpha}
          setCvarAlpha={setCvarAlpha}
          riskAversion={riskAversion}
          setRiskAversion={setRiskAversion}
          expRiskAversion={expRiskAversion}
          setExpRiskAversion={setExpRiskAversion}
          constraintType={constraintType}
          setConstraintType={setConstraintType}
          maxVolatility={maxVolatility}
          setMaxVolatility={setMaxVolatility}
          maxCvar={maxCvar}
          setMaxCvar={setMaxCvar}
          cvarConstraintAlpha={cvarConstraintAlpha}
          setCvarConstraintAlpha={setCvarConstraintAlpha}
          dataInfo={dataInfo}
          onUpload={handleUpload}
          onResetData={handleResetData}
          isUploading={isUploading}
          onOptimize={runOptimization}
          isLoading={isLoading}
        />
      </div>

      {/* Main Content */}
      <main id="main-content" className="flex-1 flex flex-col min-h-screen overflow-hidden">
        {/* Header */}
        <header className="px-6 py-5 border-b" style={{ borderColor: '#27272a', background: 'rgba(17, 17, 19, 0.8)', backdropFilter: 'blur(12px)' }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Mobile menu button */}
              {isMobile && (
                <button
                  onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                  className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                  aria-label={isSidebarOpen ? 'Close menu' : 'Open menu'}
                  aria-expanded={isSidebarOpen}
                >
                  {isSidebarOpen ? <X className="w-6 h-6 text-white" /> : <Menu className="w-6 h-6 text-white" />}
                </button>
              )}
              <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)', boxShadow: '0 4px 14px rgba(16, 185, 129, 0.35)' }}>
                <TrendingUp className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Portfolio Optimizer</h1>
                <p className="text-sm text-gray-400">
                  Scenario-based optimization • {dataInfo ? `${dataInfo.n_scenarios.toLocaleString()} simulations` : '10,000 simulations'}
                  {dataInfo?.isCustom && <span className="text-teal-400 ml-2">• Custom Data</span>}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Keyboard shortcut hint */}
              <span className="hidden lg:inline-flex text-xs text-zinc-500">
                <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700 font-mono">Ctrl</kbd>
                <span className="mx-1">+</span>
                <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700 font-mono">R</kbd>
                <span className="ml-2">to run</span>
              </span>
              {result && (
                <div 
                  className="flex items-center gap-2 px-4 py-2 rounded-xl" 
                  style={{ background: result.status === 'optimal' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(251, 191, 36, 0.15)' }}
                  role="status"
                  aria-live="polite"
                >
                  <Zap className="w-4 h-4" style={{ color: result.status === 'optimal' ? '#10B981' : '#FBBF24' }} aria-hidden="true" />
                  <span className="text-sm font-semibold" style={{ color: result.status === 'optimal' ? '#10B981' : '#FBBF24' }}>
                    {result.status === 'optimal' ? 'Optimal Solution' : 'Suboptimal'}
                  </span>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Error banner */}
        {error && (
          <div className="mx-6 mt-4 p-4 rounded-xl border" style={{ background: 'rgba(239, 68, 68, 0.1)', borderColor: 'rgba(239, 68, 68, 0.3)' }} role="alert">
            <p className="text-red-400 font-medium">{error}</p>
          </div>
        )}

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto">
          {/* Key Metrics */}
          {result && (
            <section className="px-6 py-5" aria-label="Key Metrics">
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 grid-responsive">
                <MetricCard
                  label="No-Loss Return"
                  value={result.distribution_stats.no_loss_return}
                  format="percent"
                  type="positive"
                  tooltip={METRIC_TOOLTIPS.noLossReturn}
                />
                <MetricCard
                  label="Expected Loss"
                  value={result.distribution_stats.expected_loss}
                  format="percent"
                  type="negative"
                  tooltip={METRIC_TOOLTIPS.expectedLoss}
                />
                <MetricCard
                  label="Expected Return"
                  value={result.metrics.expected_return}
                  format="percent"
                  type={result.metrics.expected_return >= 0 ? 'positive' : 'negative'}
                  tooltip={METRIC_TOOLTIPS.expectedReturn}
                />
                <MetricCard
                  label="Volatility"
                  value={result.metrics.volatility}
                  format="percent"
                  type="neutral"
                  tooltip={METRIC_TOOLTIPS.volatility}
                />
                <MetricCard
                  label="VaR 90%"
                  value={result.metrics.var_90}
                  format="percent"
                  type="warning"
                  tooltip={METRIC_TOOLTIPS.var90}
                />
                <MetricCard
                  label="TVaR 90%"
                  value={result.metrics.cvar_90}
                  format="percent"
                  type="negative"
                  tooltip={METRIC_TOOLTIPS.tvar90}
                />
                <MetricCard
                  label="VaR 99%"
                  value={result.metrics.var_99}
                  format="percent"
                  type="warning"
                  tooltip={METRIC_TOOLTIPS.var99}
                />
                <MetricCard
                  label="TVaR 99%"
                  value={result.metrics.cvar_99}
                  format="percent"
                  type="negative"
                  tooltip={METRIC_TOOLTIPS.tvar99}
                />
              </div>
            </section>
          )}

          {/* Tabs */}
          <nav className="px-6 pb-4" aria-label="Result tabs">
            <div className="inline-flex gap-1 p-1.5 rounded-xl" style={{ background: '#18181b' }} role="tablist">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`tab-button flex items-center gap-2 ${activeTab === tab.id ? 'active' : ''}`}
                  role="tab"
                  aria-selected={activeTab === tab.id}
                  aria-controls={`tabpanel-${tab.id}`}
                  id={`tab-${tab.id}`}
                >
                  <tab.icon className="w-4 h-4" aria-hidden="true" />
                  {tab.label}
                </button>
              ))}
            </div>
          </nav>

          {/* Tab Content */}
          <div className="px-6 pb-6">
            {isLoading ? (
              <PageSkeleton />
            ) : result ? (
              <ErrorBoundary>
                <div 
                  className="animate-fadeIn"
                  role="tabpanel"
                  id={`tabpanel-${activeTab}`}
                  aria-labelledby={`tab-${activeTab}`}
                >
                  {activeTab === 'distribution' && <DistributionTab result={result} />}
                  {activeTab === 'allocation' && <AllocationTab result={result} assets={assets} />}
                  {activeTab === 'risk' && <RiskAnalysisTab result={result} frontier={frontier} />}
                  {activeTab === 'stats' && <StatsTab result={result} />}
                </div>
              </ErrorBoundary>
            ) : (
              <div className="flex items-center justify-center h-64">
                <p className="text-gray-500">Click "Run Optimization" to get started</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// Wrap with providers
function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
