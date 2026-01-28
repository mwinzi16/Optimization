import { useState, useCallback } from 'react';
import { Settings, Play, TrendingUp, Shield, BarChart2, Sparkles, Upload, X, Database } from 'lucide-react';
import { OptimizationMethod } from '../types';

interface DataInfo {
  n_assets: number;
  n_scenarios: number;
  asset_names: string[];
  isCustom: boolean;
}

interface SidebarProps {
  method: OptimizationMethod;
  setMethod: (m: OptimizationMethod) => void;
  minWeight: number;
  setMinWeight: (v: number) => void;
  maxWeight: number;
  setMaxWeight: (v: number) => void;
  riskFreeRate: number;
  setRiskFreeRate: (v: number) => void;
  cvarAlpha: number;
  setCvarAlpha: (v: number) => void;
  riskAversion: number;
  setRiskAversion: (v: number) => void;
  expRiskAversion: number;
  setExpRiskAversion: (v: number) => void;
  constraintType: 'volatility' | 'cvar';
  setConstraintType: (v: 'volatility' | 'cvar') => void;
  maxVolatility: number;
  setMaxVolatility: (v: number) => void;
  maxCvar: number;
  setMaxCvar: (v: number) => void;
  cvarConstraintAlpha: number;
  setCvarConstraintAlpha: (v: number) => void;
  dataInfo: DataInfo | null;
  onUpload: (file: File) => Promise<void>;
  onResetData: () => Promise<void>;
  isUploading: boolean;
  onOptimize: () => void;
  isLoading: boolean;
}

const METHODS: OptimizationMethod[] = [
  'Maximum Sharpe Ratio',
  'Minimum Variance',
  'Minimum CVaR',
  'Mean-CVaR Trade-off',
  'Maximum Return (Constrained)',
  'Exponential Utility (CARA)',
];

export default function Sidebar({
  method,
  setMethod,
  minWeight,
  setMinWeight,
  maxWeight,
  setMaxWeight,
  riskFreeRate,
  setRiskFreeRate,
  cvarAlpha,
  setCvarAlpha,
  riskAversion,
  setRiskAversion,
  expRiskAversion,
  setExpRiskAversion,
  constraintType,
  setConstraintType,
  maxVolatility,
  setMaxVolatility,
  maxCvar,
  setMaxCvar,
  cvarConstraintAlpha,
  setCvarConstraintAlpha,
  dataInfo,
  onUpload,
  onResetData,
  isUploading,
  onOptimize,
  isLoading,
}: SidebarProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
      onUpload(file);
    }
  }, [onUpload]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
    }
    e.target.value = ''; // Reset input
  }, [onUpload]);

  return (
    <aside 
      className="w-80 flex flex-col h-screen overflow-hidden"
      style={{ 
        background: 'linear-gradient(180deg, #111113 0%, #0d0d0f 100%)',
        borderRight: '1px solid rgba(255,255,255,0.06)'
      }}
    >
      {/* Header */}
      <div 
        className="p-5"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
      >
        <div className="flex items-center gap-3">
          <div 
            className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, rgba(20,184,166,0.2) 0%, rgba(16,185,129,0.2) 100%)' }}
          >
            <Settings className="w-5 h-5 text-teal-400" />
          </div>
          <div>
            <span className="font-semibold text-white text-sm">Settings</span>
            <p className="text-xs text-zinc-500">Configure optimization</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {/* Data Upload Section */}
        <div>
          <label className="flex items-center gap-2 text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">
            <Database className="w-3.5 h-3.5 text-teal-500" />
            Data Source
          </label>
          
          {/* File Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className="relative rounded-lg transition-all cursor-pointer"
            style={{
              background: isDragOver 
                ? 'rgba(20,184,166,0.15)' 
                : 'rgba(255,255,255,0.02)',
              border: isDragOver 
                ? '2px dashed rgba(20,184,166,0.6)' 
                : '2px dashed rgba(255,255,255,0.1)',
            }}
          >
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="p-4 text-center">
              {isUploading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-teal-400 border-t-transparent rounded-full animate-spin" />
                  <span className="text-xs text-zinc-400">Uploading...</span>
                </div>
              ) : (
                <>
                  <Upload className="w-6 h-6 mx-auto mb-2 text-zinc-500" />
                  <p className="text-xs text-zinc-400">
                    Drop CSV/Excel file or <span className="text-teal-400">browse</span>
                  </p>
                  <p className="text-[10px] text-zinc-600 mt-1">Rows = scenarios, Cols = assets</p>
                </>
              )}
            </div>
          </div>

          {/* Data Info Display */}
          {dataInfo && (
            <div 
              className="mt-2 p-3 rounded-lg"
              style={{ 
                background: dataInfo.isCustom 
                  ? 'linear-gradient(135deg, rgba(20,184,166,0.1) 0%, rgba(16,185,129,0.05) 100%)'
                  : 'rgba(255,255,255,0.02)',
                border: dataInfo.isCustom 
                  ? '1px solid rgba(20,184,166,0.3)'
                  : '1px solid rgba(255,255,255,0.06)'
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${dataInfo.isCustom ? 'bg-teal-400' : 'bg-zinc-500'}`} />
                  <span className="text-xs font-medium text-white">
                    {dataInfo.isCustom ? 'Custom Data' : 'Sample Data'}
                  </span>
                </div>
                {dataInfo.isCustom && (
                  <button
                    onClick={onResetData}
                    className="p-1 rounded hover:bg-white/10 transition-colors"
                    title="Reset to sample data"
                  >
                    <X className="w-3 h-3 text-zinc-500" />
                  </button>
                )}
              </div>
              <div className="mt-2 grid grid-cols-2 gap-2 text-[10px]">
                <div>
                  <span className="text-zinc-500">Assets: </span>
                  <span className="text-zinc-300 font-medium">{dataInfo.n_assets.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-zinc-500">Scenarios: </span>
                  <span className="text-zinc-300 font-medium">{dataInfo.n_scenarios.toLocaleString()}</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Optimization Method */}
        <div>
          <label className="flex items-center gap-2 text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">
            <TrendingUp className="w-3.5 h-3.5 text-teal-500" />
            Method
          </label>
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value as OptimizationMethod)}
            className="w-full px-3 py-2.5 rounded-lg text-sm text-white transition-all cursor-pointer"
            style={{ 
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.08)',
              outline: 'none'
            }}
            onFocus={(e) => e.target.style.borderColor = 'rgba(20,184,166,0.5)'}
            onBlur={(e) => e.target.style.borderColor = 'rgba(255,255,255,0.08)'}
          >
            {METHODS.map((m) => (
              <option key={m} value={m} style={{ background: '#1a1a1c', color: '#e4e4e7' }}>{m}</option>
            ))}
          </select>
          
          {/* Method Description */}
          <div 
            className="mt-3 rounded-lg p-3"
            style={{ 
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.06)'
            }}
          >
            {method === 'Maximum Sharpe Ratio' && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-teal-400" />
                  <span className="text-xs font-semibold text-white">Sharpe Ratio Optimization</span>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Maximizes the ratio of expected return to volatility. Finds the portfolio with the best risk-adjusted return.
                </p>
                <div className="font-mono text-xs text-zinc-500 bg-black/30 rounded px-2 py-1">
                  max (μₚ - rᶠ) / σₚ
                </div>
                {/* Mini visualization - Sharpe Ratio */}
                <svg viewBox="0 0 100 50" className="w-full h-12 mt-2">
                  <line x1="10" y1="45" x2="90" y2="45" stroke="#3f3f46" strokeWidth="1" />
                  <line x1="10" y1="5" x2="10" y2="45" stroke="#3f3f46" strokeWidth="1" />
                  <path d="M 10,45 Q 30,30 50,20 T 85,10" fill="none" stroke="#14B8A6" strokeWidth="1.5" />
                  <line x1="10" y1="45" x2="50" y2="20" stroke="#10B981" strokeWidth="1" strokeDasharray="3,2" />
                  <circle cx="50" cy="20" r="3" fill="#10B981" />
                  <text x="55" y="22" fill="#10B981" fontSize="6">Optimal</text>
                  <text x="45" y="50" fill="#71717a" fontSize="5">Risk (σ)</text>
                  <text x="2" y="25" fill="#71717a" fontSize="5" transform="rotate(-90, 8, 25)">Return</text>
                </svg>
              </div>
            )}
            
            {method === 'Minimum Variance' && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-teal-400" />
                  <span className="text-xs font-semibold text-white">Minimum Variance</span>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Minimizes portfolio volatility regardless of expected return. Best for highly risk-averse investors.
                </p>
                <div className="font-mono text-xs text-zinc-500 bg-black/30 rounded px-2 py-1">
                  min σₚ² = wᵀΣw
                </div>
                {/* Mini visualization - Variance */}
                <svg viewBox="0 0 100 50" className="w-full h-12 mt-2">
                  <line x1="10" y1="45" x2="90" y2="45" stroke="#3f3f46" strokeWidth="1" />
                  <line x1="10" y1="5" x2="10" y2="45" stroke="#3f3f46" strokeWidth="1" />
                  <path d="M 15,35 Q 25,40 35,38 T 55,25 T 85,10" fill="none" stroke="#14B8A6" strokeWidth="1.5" />
                  <circle cx="15" cy="35" r="3" fill="#10B981" />
                  <text x="8" y="32" fill="#10B981" fontSize="6">Min σ</text>
                  <text x="45" y="50" fill="#71717a" fontSize="5">Risk (σ)</text>
                </svg>
              </div>
            )}
            
            {method === 'Minimum CVaR' && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-amber-400" />
                  <span className="text-xs font-semibold text-white">Minimum CVaR</span>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Minimizes Conditional Value-at-Risk (expected loss in worst scenarios). Focuses on tail risk protection.
                </p>
                <div className="font-mono text-xs text-zinc-500 bg-black/30 rounded px-2 py-1">
                  min E[Loss | Loss &gt; VaRₐ]
                </div>
                {/* Mini visualization - CVaR tail */}
                <svg viewBox="0 0 100 50" className="w-full h-12 mt-2">
                  <path d="M 5,40 Q 20,5 50,10 T 95,40" fill="none" stroke="#14B8A6" strokeWidth="1.5" />
                  <path d="M 5,40 Q 15,15 25,25 L 25,40 Z" fill="rgba(248,113,113,0.3)" stroke="#F87171" strokeWidth="1" />
                  <line x1="25" y1="5" x2="25" y2="40" stroke="#FBBF24" strokeWidth="1" strokeDasharray="2,2" />
                  <text x="27" y="10" fill="#FBBF24" fontSize="5">VaR</text>
                  <text x="8" y="35" fill="#F87171" fontSize="5">CVaR</text>
                </svg>
              </div>
            )}
            
            {method === 'Mean-CVaR Trade-off' && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-teal-400" />
                  <span className="text-xs font-semibold text-white">Mean-CVaR Trade-off</span>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Balances expected return against tail risk. Higher λ = more focus on minimizing CVaR.
                </p>
                <div className="font-mono text-xs text-zinc-500 bg-black/30 rounded px-2 py-1">
                  max μₚ - λ · CVaRₐ
                </div>
                {/* Mini visualization - Trade-off */}
                <svg viewBox="0 0 100 50" className="w-full h-12 mt-2">
                  <line x1="10" y1="45" x2="90" y2="45" stroke="#3f3f46" strokeWidth="1" />
                  <line x1="10" y1="5" x2="10" y2="45" stroke="#3f3f46" strokeWidth="1" />
                  <path d="M 10,10 L 85,40" fill="none" stroke="#F87171" strokeWidth="1" strokeDasharray="2,2" />
                  <path d="M 10,40 L 85,15" fill="none" stroke="#10B981" strokeWidth="1" strokeDasharray="2,2" />
                  <circle cx="45" cy="27" r="3" fill="#14B8A6" />
                  <text x="50" y="29" fill="#14B8A6" fontSize="5">λ balance</text>
                  <text x="75" y="13" fill="#10B981" fontSize="5">Return</text>
                  <text x="75" y="43" fill="#F87171" fontSize="5">CVaR</text>
                </svg>
              </div>
            )}
            
            {method === 'Maximum Return (Constrained)' && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-semibold text-white">Constrained Maximum Return</span>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Maximizes expected return subject to a risk constraint (volatility or CVaR limit).
                </p>
                <div className="font-mono text-xs text-zinc-500 bg-black/30 rounded px-2 py-1">
                  max μₚ s.t. σₚ ≤ σₘₐₓ
                </div>
                {/* Mini visualization - Constrained */}
                <svg viewBox="0 0 100 50" className="w-full h-12 mt-2">
                  <line x1="10" y1="45" x2="90" y2="45" stroke="#3f3f46" strokeWidth="1" />
                  <line x1="10" y1="5" x2="10" y2="45" stroke="#3f3f46" strokeWidth="1" />
                  <path d="M 15,40 Q 30,30 45,22 T 85,8" fill="none" stroke="#14B8A6" strokeWidth="1.5" />
                  <line x1="55" y1="5" x2="55" y2="45" stroke="#FBBF24" strokeWidth="2" />
                  <circle cx="55" cy="17" r="3" fill="#10B981" />
                  <text x="58" y="10" fill="#FBBF24" fontSize="5">σ limit</text>
                  <text x="58" y="19" fill="#10B981" fontSize="5">max μ</text>
                </svg>
              </div>
            )}
            
            {method === 'Exponential Utility (CARA)' && (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-violet-400" />
                  <span className="text-xs font-semibold text-white">Exponential Utility (CARA)</span>
                </div>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Maximizes expected utility with constant absolute risk aversion. The concave curve shows diminishing marginal utility—losses hurt more than equivalent gains satisfy.
                </p>
                <div className="font-mono text-xs text-zinc-500 bg-black/30 rounded px-2 py-1">
                  max E[-e<sup>-C·W</sup>]
                </div>
                {/* Mini visualization - Exponential Utility curve U(W) = -e^(-CW) */}
                <svg viewBox="0 0 100 60" className="w-full h-14 mt-2">
                  {/* Axes */}
                  <line x1="10" y1="35" x2="95" y2="35" stroke="#3f3f46" strokeWidth="0.5" />
                  <line x1="50" y1="5" x2="50" y2="55" stroke="#3f3f46" strokeWidth="0.5" />
                  {/* Zero line for utility */}
                  <line x1="10" y1="12" x2="95" y2="12" stroke="#3f3f46" strokeWidth="0.5" strokeDasharray="2,2" />
                  {/* Exponential utility curve: steep on left, flattens approaching 0 on right */}
                  <path d="M 10,55 C 25,50 35,40 50,30 S 75,15 95,13" fill="none" stroke="#A78BFA" strokeWidth="2" />
                  {/* Reference: linear utility for comparison */}
                  <path d="M 10,55 L 95,10" fill="none" stroke="#3f3f46" strokeWidth="0.5" strokeDasharray="3,3" />
                  {/* Highlight the concavity - losses region */}
                  <path d="M 10,55 C 25,50 35,40 50,30" fill="none" stroke="#F87171" strokeWidth="2" />
                  {/* Labels */}
                  <text x="12" y="53" fill="#F87171" fontSize="5">Losses</text>
                  <text x="75" y="22" fill="#10B981" fontSize="5">Gains</text>
                  <text x="92" y="10" fill="#3f3f46" fontSize="4">U=0</text>
                  <text x="52" y="55" fill="#71717a" fontSize="4">W=0</text>
                  <text x="80" y="18" fill="#A78BFA" fontSize="5">U(W)</text>
                  {/* Arrow showing "steep here" */}
                  <text x="22" y="40" fill="#F87171" fontSize="4">steep</text>
                  <text x="70" y="15" fill="#71717a" fontSize="4">flat</text>
                </svg>
                <p className="text-xs text-zinc-500 italic">
                  Curve shows U(W) = -e<sup>-CW</sup>: steeper slope for losses vs gains
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Method-specific parameters */}
        {method === 'Minimum CVaR' && (
          <div className="space-y-2">
            <label className="text-xs font-medium text-zinc-400">CVaR Confidence Level</label>
            <input
              type="range"
              min={90}
              max={99}
              value={cvarAlpha}
              onChange={(e) => setCvarAlpha(Number(e.target.value))}
              className="w-full styled-range"
            />
            <div className="flex justify-between text-xs">
              <span className="text-zinc-600">90%</span>
              <span className="font-semibold text-teal-400">{cvarAlpha}%</span>
              <span className="text-zinc-600">99%</span>
            </div>
          </div>
        )}

        {method === 'Mean-CVaR Trade-off' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400">Risk Aversion (λ)</label>
              <input
                type="range"
                min={0.1}
                max={5}
                step={0.1}
                value={riskAversion}
                onChange={(e) => setRiskAversion(Number(e.target.value))}
                className="w-full styled-range"
              />
              <div className="flex justify-between text-xs">
                <span className="text-zinc-600">Low</span>
                <span className="font-semibold text-teal-400">{riskAversion.toFixed(1)}</span>
                <span className="text-zinc-600">High</span>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400">CVaR Confidence Level</label>
              <input
                type="range"
                min={90}
                max={99}
                value={cvarAlpha}
                onChange={(e) => setCvarAlpha(Number(e.target.value))}
                className="w-full styled-range"
              />
              <div className="flex justify-between text-xs">
                <span className="text-zinc-600">90%</span>
                <span className="font-semibold text-teal-400">{cvarAlpha}%</span>
                <span className="text-zinc-600">99%</span>
              </div>
            </div>
          </div>
        )}

        {method === 'Maximum Return (Constrained)' && (
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-zinc-400 mb-2 block">Constraint Type</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setConstraintType('volatility')}
                  className="flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-all"
                  style={{
                    background: constraintType === 'volatility' 
                      ? 'linear-gradient(135deg, rgba(20,184,166,0.3) 0%, rgba(16,185,129,0.3) 100%)'
                      : 'rgba(255,255,255,0.04)',
                    border: constraintType === 'volatility' 
                      ? '1px solid rgba(20,184,166,0.5)'
                      : '1px solid rgba(255,255,255,0.08)',
                    color: constraintType === 'volatility' ? '#5eead4' : '#71717a'
                  }}
                >
                  Volatility
                </button>
                <button
                  onClick={() => setConstraintType('cvar')}
                  className="flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-all"
                  style={{
                    background: constraintType === 'cvar' 
                      ? 'linear-gradient(135deg, rgba(20,184,166,0.3) 0%, rgba(16,185,129,0.3) 100%)'
                      : 'rgba(255,255,255,0.04)',
                    border: constraintType === 'cvar' 
                      ? '1px solid rgba(20,184,166,0.5)'
                      : '1px solid rgba(255,255,255,0.08)',
                    color: constraintType === 'cvar' ? '#5eead4' : '#71717a'
                  }}
                >
                  CVaR
                </button>
              </div>
            </div>
            {constraintType === 'volatility' ? (
              <div className="space-y-2">
                <label className="text-xs font-medium text-zinc-400">Max Volatility</label>
                <input
                  type="range"
                  min={5}
                  max={30}
                  step={0.5}
                  value={maxVolatility}
                  onChange={(e) => setMaxVolatility(Number(e.target.value))}
                  className="w-full styled-range"
                />
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-600">5%</span>
                  <span className="font-semibold text-teal-400">{maxVolatility}%</span>
                  <span className="text-zinc-600">30%</span>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs font-medium text-zinc-400">CVaR Confidence Level</label>
                  <div className="flex gap-1">
                    {[90, 95, 98, 99].map((level) => (
                      <button
                        key={level}
                        onClick={() => setCvarConstraintAlpha(level)}
                        className="flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all"
                        style={{
                          background: cvarConstraintAlpha === level 
                            ? 'linear-gradient(135deg, rgba(20,184,166,0.3) 0%, rgba(16,185,129,0.3) 100%)'
                            : 'rgba(255,255,255,0.04)',
                          border: cvarConstraintAlpha === level 
                            ? '1px solid rgba(20,184,166,0.5)'
                            : '1px solid rgba(255,255,255,0.08)',
                          color: cvarConstraintAlpha === level ? '#5eead4' : '#71717a'
                        }}
                      >
                        {level}%
                      </button>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-medium text-zinc-400">Max CVaR Loss</label>
                  <input
                    type="range"
                    min={10}
                    max={50}
                    step={1}
                    value={maxCvar}
                    onChange={(e) => setMaxCvar(Number(e.target.value))}
                    className="w-full styled-range"
                  />
                  <div className="flex justify-between text-xs">
                    <span className="text-zinc-600">10%</span>
                    <span className="font-semibold text-teal-400">{maxCvar}%</span>
                    <span className="text-zinc-600">50%</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {method === 'Exponential Utility (CARA)' && (
          <div className="space-y-4">
            <div 
              className="rounded-xl p-4"
              style={{ 
                background: 'linear-gradient(135deg, rgba(20,184,166,0.1) 0%, rgba(16,185,129,0.05) 100%)',
                border: '1px solid rgba(20,184,166,0.2)'
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-teal-400" />
                <span className="text-xs font-semibold text-teal-300">Elton/Gruber Utility</span>
              </div>
              <div className="font-mono text-xs text-zinc-400 space-y-1">
                <p>U(W) = -e<sup>-C·W</sup></p>
                <p>V = -e<sup>-C·50·r</sup> / C</p>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-medium text-zinc-400">Risk Aversion (C)</label>
              <input
                type="range"
                min={0.01}
                max={1}
                step={0.01}
                value={expRiskAversion}
                onChange={(e) => setExpRiskAversion(Number(e.target.value))}
                className="w-full styled-range"
              />
              <div className="flex justify-between text-xs">
                <span className="text-zinc-600">Neutral</span>
                <span className="font-semibold text-teal-400">{expRiskAversion.toFixed(2)}</span>
                <span className="text-zinc-600">Averse</span>
              </div>
            </div>
          </div>
        )}

        {/* Weight Constraints */}
        <div 
          className="pt-5"
          style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
        >
          <label className="flex items-center gap-2 text-xs font-medium text-zinc-400 uppercase tracking-wider mb-3">
            <Shield className="w-3.5 h-3.5 text-emerald-500" />
            Weight Constraints
          </label>
          
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-zinc-500 mb-1.5 block">Min Weight</label>
              <div className="relative">
                <input
                  type="number"
                  min={0}
                  max={50}
                  value={minWeight}
                  onChange={(e) => setMinWeight(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg text-sm text-white pr-8"
                  style={{ 
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    outline: 'none'
                  }}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-500">%</span>
              </div>
            </div>
            <div>
              <label className="text-xs text-zinc-500 mb-1.5 block">Max Weight</label>
              <div className="relative">
                <input
                  type="number"
                  min={10}
                  max={100}
                  value={maxWeight}
                  onChange={(e) => setMaxWeight(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-lg text-sm text-white pr-8"
                  style={{ 
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    outline: 'none'
                  }}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-500">%</span>
              </div>
            </div>
          </div>
          
          {/* Risk-Free Rate */}
          <div className="mt-4">
            <label className="text-xs text-zinc-500 mb-1.5 block">Risk-Free Rate (embedded in returns)</label>
            <div className="relative">
              <input
                type="number"
                min={0}
                max={20}
                step={0.1}
                value={riskFreeRate}
                onChange={(e) => setRiskFreeRate(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg text-sm text-white pr-8"
                style={{ 
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  outline: 'none'
                }}
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-500">%</span>
            </div>
            <p className="text-xs text-zinc-600 mt-1 italic">Subtracted from scenario returns</p>
          </div>
        </div>

        {/* Info box */}
        <div 
          className="rounded-xl p-4"
          style={{ 
            background: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.06)'
          }}
        >
          <div className="flex items-center gap-2 mb-2">
            <BarChart2 className="w-4 h-4 text-zinc-500" />
            <span className="text-xs font-medium text-zinc-400">Simulation Info</span>
          </div>
          <div className="space-y-1 text-xs text-zinc-500">
            <p>• Risk-Free Rate: <span className="text-zinc-300">{riskFreeRate}%</span></p>
            <p>• Scenarios: <span className="text-zinc-300">10,000</span></p>
          </div>
        </div>
      </div>

      {/* Run Button */}
      <div 
        className="p-5"
        style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}
      >
        <button
          onClick={onOptimize}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-3.5 px-4 rounded-xl font-semibold text-white transition-all"
          style={{ 
            background: isLoading 
              ? 'rgba(255,255,255,0.1)' 
              : 'linear-gradient(135deg, #14B8A6 0%, #10B981 100%)',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            boxShadow: isLoading ? 'none' : '0 0 20px rgba(20,184,166,0.3)'
          }}
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
              <span className="text-zinc-400">Optimizing...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Run Optimization
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
