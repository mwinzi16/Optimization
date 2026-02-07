import { useState, useCallback, useRef } from 'react';
import {
  Upload,
  ChevronDown,
  ChevronUp,
  Play,
  RotateCcw,
  Info,
  X,
  Loader2,
} from 'lucide-react';
import { useOptimizationStore } from '../stores/optimizationStore';
import { useDataStore } from '../stores/dataStore';
import { useUiStore } from '../stores/uiStore';
import { METHODS, METHOD_INFO } from '../utils/constants';
import { METRIC_CARD_VARIANTS } from '../utils/colors';
import { formatPercent, formatRatio } from '../utils/format';
import { MetricCard } from './MetricCard';
import type { OptimizationMethod } from '../types';

export function Sidebar() {
  const optStore = useOptimizationStore();
  const dataStore = useDataStore();
  const { showMobileSidebar, toggleMobileSidebar, addToast } = useUiStore();

  const [isDragOver, setIsDragOver] = useState(false);
  const [showMethodInfo, setShowMethodInfo] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const methodInfo = METHOD_INFO[optStore.method];

  // Drag & drop handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) await handleFileUpload(file);
    },
    [],
  );

  const handleFileUpload = async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'csv' && ext !== 'xlsx') {
      addToast({ type: 'error', message: 'Only .csv and .xlsx files are supported.' });
      return;
    }
    try {
      await dataStore.uploadFile(file);
      addToast({ type: 'success', message: `Uploaded ${file.name} successfully.` });
    } catch {
      addToast({ type: 'error', message: 'File upload failed. Please try again.' });
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file);
    e.target.value = '';
  };

  const handleOptimize = async () => {
    try {
      await optStore.runOptimization();
      optStore.fetchFrontier();
      addToast({ type: 'success', message: 'Optimization completed successfully.' });
    } catch {
      addToast({ type: 'error', message: 'Optimization failed. Check parameters.' });
    }
  };

  const handleReset = () => {
    optStore.reset();
    addToast({ type: 'info', message: 'Parameters reset to defaults.' });
  };

  const handleResetData = async () => {
    try {
      await dataStore.resetData();
      addToast({ type: 'info', message: 'Data reset to sample dataset.' });
    } catch {
      addToast({ type: 'error', message: 'Failed to reset data.' });
    }
  };

  // Determine which conditional parameters to show
  const showCvarAlpha =
    optStore.method === 'Minimum CVaR' ||
    optStore.method === 'Mean-CVaR Trade-off' ||
    (optStore.method === 'Maximum Return (Constrained)' &&
      optStore.constraintType === 'cvar');

  const showRiskAversion = optStore.method === 'Mean-CVaR Trade-off';
  const showExpRiskAversion = optStore.method === 'Exponential Utility (CARA)';
  const showConstraint = optStore.method === 'Maximum Return (Constrained)';

  const sidebarContent = (
    <div className="flex h-full flex-col overflow-y-auto bg-bg-secondary p-4">
      {/* Mobile close button */}
      <div className="mb-4 flex items-center justify-between lg:hidden">
        <span className="text-sm font-semibold text-text-primary">Settings</span>
        <button
          onClick={toggleMobileSidebar}
          className="rounded-lg p-1.5 text-text-muted hover:bg-bg-elevated hover:text-text-primary"
        >
          <X size={18} />
        </button>
      </div>

      {/* File Upload Zone */}
      <section className="mb-5">
        <p className="label-text mb-2">Data Source</p>
        <div
          className={`drop-zone ${isDragOver ? 'active' : ''}`}
          onDragOver={handleDragOver}
          onDragEnter={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          {dataStore.isUploading ? (
            <Loader2 size={24} className="animate-spin text-accent-teal" />
          ) : (
            <Upload size={24} className="text-text-muted" />
          )}
          <span className="text-xs text-text-muted">
            {dataStore.isUploading ? 'Uploading...' : 'Drop CSV/XLSX or click to upload'}
          </span>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx"
          onChange={handleFileSelect}
          className="hidden"
        />
        {dataStore.dataSource !== 'sample' && (
          <div className="mt-2 flex items-center justify-between">
            <span className="truncate text-xs text-text-secondary">
              {dataStore.dataSource}
            </span>
            <button
              onClick={handleResetData}
              className="shrink-0 text-xs text-accent-teal hover:underline"
            >
              Reset to Sample
            </button>
          </div>
        )}
      </section>

      {/* Method Selector */}
      <section className="mb-5">
        <label className="label-text mb-2 block">Optimization Method</label>
        <select
          value={optStore.method}
          onChange={(e) => optStore.setMethod(e.target.value as OptimizationMethod)}
          className="input-field"
        >
          {METHODS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        {/* Method Info Toggle */}
        <button
          onClick={() => setShowMethodInfo(!showMethodInfo)}
          className="mt-2 flex w-full items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors"
        >
          <Info size={12} />
          <span>Methodology</span>
          {showMethodInfo ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        </button>

        {showMethodInfo && (
          <div className="mt-2 animate-fade-in rounded-lg bg-bg-elevated p-3 text-xs leading-relaxed">
            <p className="mb-1 font-semibold text-accent-teal">{methodInfo.goal}</p>
            <p className="mb-2 text-text-secondary">{methodInfo.description}</p>
            <div className="mb-2 rounded bg-bg-primary px-2 py-1.5 font-mono text-accent-gold">
              {methodInfo.formula}
            </div>
            <p className="text-text-muted">
              <span className="font-medium text-text-secondary">Best for:</span>{' '}
              {methodInfo.bestFor}
            </p>
          </div>
        )}
      </section>

      {/* Parameters */}
      <section className="mb-5 space-y-3">
        <p className="label-text">Parameters</p>

        {/* Min Weight */}
        <div>
          <label className="mb-1 flex items-center justify-between text-xs text-text-secondary">
            <span>Min Weight</span>
            <span className="font-mono text-text-muted">{optStore.minWeight.toFixed(2)}</span>
          </label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={optStore.minWeight}
            onChange={(e) => optStore.setMinWeight(Number(e.target.value))}
            className="w-full accent-accent-teal"
          />
        </div>

        {/* Max Weight */}
        <div>
          <label className="mb-1 flex items-center justify-between text-xs text-text-secondary">
            <span>Max Weight</span>
            <span className="font-mono text-text-muted">{optStore.maxWeight.toFixed(2)}</span>
          </label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={optStore.maxWeight}
            onChange={(e) => optStore.setMaxWeight(Number(e.target.value))}
            className="w-full accent-accent-teal"
          />
        </div>

        {/* Risk-Free Rate */}
        <div>
          <label className="mb-1 flex items-center justify-between text-xs text-text-secondary">
            <span>Risk-Free Rate</span>
            <span className="font-mono text-text-muted">
              {(optStore.riskFreeRate * 100).toFixed(1)}%
            </span>
          </label>
          <input
            type="range"
            min={0}
            max={0.1}
            step={0.001}
            value={optStore.riskFreeRate}
            onChange={(e) => optStore.setRiskFreeRate(Number(e.target.value))}
            className="w-full accent-accent-teal"
          />
        </div>

        {/* CVaR Alpha */}
        {showCvarAlpha && (
          <div className="animate-fade-in">
            <label className="mb-1 flex items-center justify-between text-xs text-text-secondary">
              <span>CVaR Alpha</span>
              <span className="font-mono text-text-muted">
                {(optStore.cvarAlpha * 100).toFixed(0)}%
              </span>
            </label>
            <input
              type="range"
              min={0.01}
              max={0.2}
              step={0.01}
              value={optStore.cvarAlpha}
              onChange={(e) => optStore.setCvarAlpha(Number(e.target.value))}
              className="w-full accent-accent-teal"
            />
          </div>
        )}

        {/* Risk Aversion (Mean-CVaR) */}
        {showRiskAversion && (
          <div className="animate-fade-in">
            <label className="mb-1 flex items-center justify-between text-xs text-text-secondary">
              <span>Risk Aversion (λ)</span>
              <span className="font-mono text-text-muted">
                {optStore.riskAversion.toFixed(1)}
              </span>
            </label>
            <input
              type="range"
              min={0}
              max={10}
              step={0.1}
              value={optStore.riskAversion}
              onChange={(e) => optStore.setRiskAversion(Number(e.target.value))}
              className="w-full accent-accent-teal"
            />
          </div>
        )}

        {/* Exp Risk Aversion (CARA) */}
        {showExpRiskAversion && (
          <div className="animate-fade-in">
            <label className="mb-1 flex items-center justify-between text-xs text-text-secondary">
              <span>Risk Aversion (c)</span>
              <span className="font-mono text-text-muted">
                {optStore.expRiskAversion.toFixed(2)}
              </span>
            </label>
            <input
              type="range"
              min={0.01}
              max={5}
              step={0.01}
              value={optStore.expRiskAversion}
              onChange={(e) => optStore.setExpRiskAversion(Number(e.target.value))}
              className="w-full accent-accent-teal"
            />
          </div>
        )}

        {/* Constraint Type + Value (Max Return Constrained) */}
        {showConstraint && (
          <div className="animate-fade-in space-y-3">
            <div>
              <label className="label-text mb-1 block">Constraint Type</label>
              <select
                value={optStore.constraintType}
                onChange={(e) =>
                  optStore.setConstraintType(e.target.value as 'volatility' | 'cvar')
                }
                className="input-field"
              >
                <option value="volatility">Max Volatility</option>
                <option value="cvar">Max CVaR</option>
              </select>
            </div>

            {optStore.constraintType === 'volatility' ? (
              <div>
                <label className="mb-1 flex items-center justify-between text-xs text-text-secondary">
                  <span>Max Volatility</span>
                  <span className="font-mono text-text-muted">
                    {(optStore.maxVolatility * 100).toFixed(1)}%
                  </span>
                </label>
                <input
                  type="range"
                  min={0.01}
                  max={0.5}
                  step={0.01}
                  value={optStore.maxVolatility}
                  onChange={(e) => optStore.setMaxVolatility(Number(e.target.value))}
                  className="w-full accent-accent-teal"
                />
              </div>
            ) : (
              <div>
                <label className="mb-1 flex items-center justify-between text-xs text-text-secondary">
                  <span>Max CVaR</span>
                  <span className="font-mono text-text-muted">
                    {(optStore.maxCvar * 100).toFixed(1)}%
                  </span>
                </label>
                <input
                  type="range"
                  min={0.01}
                  max={1}
                  step={0.01}
                  value={optStore.maxCvar}
                  onChange={(e) => optStore.setMaxCvar(Number(e.target.value))}
                  className="w-full accent-accent-teal"
                />
              </div>
            )}
          </div>
        )}
      </section>

      {/* Action Buttons */}
      <section className="mb-5 space-y-2">
        <button
          onClick={handleOptimize}
          disabled={optStore.isOptimizing || !dataStore.isDataLoaded}
          className="btn-primary flex items-center justify-center gap-2"
        >
          {optStore.isOptimizing ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Play size={16} />
          )}
          {optStore.isOptimizing ? 'Optimizing...' : 'Run Optimization'}
        </button>
        <button onClick={handleReset} className="btn-secondary flex items-center justify-center gap-2">
          <RotateCcw size={14} />
          Reset
        </button>
      </section>

      {/* Result Metric Cards */}
      {optStore.result && (
        <section className="animate-fade-in">
          <p className="label-text mb-2">Results</p>
          <div className="grid grid-cols-2 gap-2">
            <MetricCard
              label="Expected Return"
              value={formatPercent(optStore.result.metrics.expected_return)}
              gradient={METRIC_CARD_VARIANTS.positive}
            />
            <MetricCard
              label="Volatility"
              value={formatPercent(optStore.result.metrics.volatility)}
              gradient={METRIC_CARD_VARIANTS.neutral}
            />
            <MetricCard
              label="Sharpe Ratio"
              value={formatRatio(optStore.result.metrics.sharpe_ratio)}
              gradient={METRIC_CARD_VARIANTS.positive}
            />
            <MetricCard
              label="CVaR 95%"
              value={formatPercent(optStore.result.metrics.cvar_95)}
              gradient={METRIC_CARD_VARIANTS.negative}
            />
            <MetricCard
              label="Worst Scenario"
              value={formatPercent(optStore.result.metrics.worst_scenario)}
              gradient={METRIC_CARD_VARIANTS.negative}
            />
            <MetricCard
              label="Skewness"
              value={formatRatio(optStore.result.distribution_stats.skewness)}
              gradient={METRIC_CARD_VARIANTS.warning}
            />
          </div>
        </section>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-[360px] shrink-0 border-r border-border-base lg:block">
        {sidebarContent}
      </aside>

      {/* Mobile overlay sidebar */}
      {showMobileSidebar && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={toggleMobileSidebar}
          />
          <aside className="absolute left-0 top-0 h-full w-[320px] animate-slide-in">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
