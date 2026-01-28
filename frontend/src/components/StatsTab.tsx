import { OptimizationResponse } from '../types';
import { Download, CheckCircle, XCircle, Copy, FileJson, Share2 } from 'lucide-react';
import { exportToCSV, exportToJSON, exportWeightsToCSV, generateShareableURL, copyToClipboard } from '../utils/export';
import { useState } from 'react';

interface StatsTabProps {
  result: OptimizationResponse;
}

// Dark theme colors
const colors = {
  card: 'rgba(255,255,255,0.02)',
  border: 'rgba(255,255,255,0.06)',
  text: '#a1a1aa',
  textMuted: '#71717a',
  white: '#e4e4e7',
  teal: '#14B8A6',
  emerald: '#10B981',
  coral: '#F87171',
  cyan: '#22D3EE',
};

export default function StatsTab({ result }: StatsTabProps) {
  const stats = result.distribution_stats;
  const metrics = result.metrics;

  const returnStats = [
    { label: 'Mean Return', value: stats.mean * 100, format: 'percent' },
    { label: 'Median Return', value: stats.median * 100, format: 'percent' },
    { label: 'No-Loss Return', value: stats.no_loss_return * 100, format: 'percent' },
    { label: 'Expected Loss', value: stats.expected_loss * 100, format: 'percent' },
    { label: 'Standard Deviation', value: stats.std * 100, format: 'percent' },
    { label: 'Skewness', value: stats.skewness, format: 'decimal' },
    { label: 'Kurtosis', value: stats.kurtosis, format: 'decimal' },
    { label: 'Minimum', value: stats.min * 100, format: 'percent' },
    { label: 'Maximum', value: stats.max * 100, format: 'percent' },
  ];

  const riskStats = [
    { label: 'VaR 90%', value: metrics.var_90 * 100, format: 'percent' },
    { label: 'CVaR 90%', value: metrics.cvar_90 * 100, format: 'percent' },
    { label: 'VaR 95%', value: metrics.var_95 * 100, format: 'percent' },
    { label: 'CVaR 95%', value: metrics.cvar_95 * 100, format: 'percent' },
    { label: 'VaR 98%', value: metrics.var_98 * 100, format: 'percent' },
    { label: 'CVaR 98%', value: metrics.cvar_98 * 100, format: 'percent' },
    { label: 'VaR 99%', value: metrics.var_99 * 100, format: 'percent' },
    { label: 'CVaR 99%', value: metrics.cvar_99 * 100, format: 'percent' },
    { label: 'Max Drawdown', value: metrics.max_drawdown * 100, format: 'percent' },
    { label: 'Sharpe Ratio', value: metrics.sharpe_ratio, format: 'decimal' },
  ];

  const probStats = [
    { label: 'Probability of Positive Return', value: stats.prob_positive * 100 },
    { label: 'Probability of Loss > 5%', value: stats.prob_loss_5 * 100 },
    { label: 'Probability of Loss > 10%', value: stats.prob_loss_10 * 100 },
    { label: 'Probability of Loss > 25%', value: stats.prob_loss_25 * 100 },
    { label: 'Probability of Loss > 50%', value: stats.prob_loss_50 * 100 },
  ];

  const formatValue = (value: number, format: string) => {
    if (format === 'percent') {
      return `${value.toFixed(2)}%`;
    }
    return value.toFixed(3);
  };

  const [copySuccess, setCopySuccess] = useState(false);

  const handleExportCSV = () => {
    exportToCSV(result);
  };

  const handleExportJSON = () => {
    exportToJSON(result);
  };

  const handleExportWeights = () => {
    exportWeightsToCSV(result.weights);
  };

  const handleCopyLink = async () => {
    const url = generateShareableURL({
      method: result.method as any,
      riskFreeRate: 0,
      minWeight: 0,
      maxWeight: 100,
      cvarAlpha: 95,
      riskAversion: 1,
      expRiskAversion: 0.5,
      constraintType: 'volatility',
      maxVolatility: 15,
      maxCvar: 25,
    });
    
    const success = await copyToClipboard(url);
    if (success) {
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-6">
        {/* Return Statistics */}
        <div 
          className="rounded-xl overflow-hidden"
          style={{ background: colors.card, border: `1px solid ${colors.border}` }}
        >
          <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
            <h3 className="font-semibold text-white">Return Statistics</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                  <th className="text-left px-6 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Metric</th>
                  <th className="text-right px-6 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Value</th>
                </tr>
              </thead>
              <tbody>
                {returnStats.map((stat) => (
                  <tr key={stat.label} style={{ borderBottom: `1px solid ${colors.border}` }} className="hover:bg-white/[0.02]">
                    <td className="px-6 py-3" style={{ color: colors.text }}>{stat.label}</td>
                    <td className="text-right px-6 py-3 font-mono" style={{ color: stat.value >= 0 ? colors.emerald : colors.coral }}>
                      {formatValue(stat.value, stat.format)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Risk Statistics */}
        <div 
          className="rounded-xl overflow-hidden"
          style={{ background: colors.card, border: `1px solid ${colors.border}` }}
        >
          <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
            <h3 className="font-semibold text-white">Risk Statistics</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                  <th className="text-left px-6 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Metric</th>
                  <th className="text-right px-6 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Value</th>
                </tr>
              </thead>
              <tbody>
                {riskStats.map((stat) => (
                  <tr key={stat.label} style={{ borderBottom: `1px solid ${colors.border}` }} className="hover:bg-white/[0.02]">
                    <td className="px-6 py-3" style={{ color: colors.text }}>{stat.label}</td>
                    <td className="text-right px-6 py-3 font-mono" style={{ 
                      color: stat.label.includes('Sharpe') 
                        ? (stat.value >= 0 ? colors.emerald : colors.coral)
                        : colors.coral
                    }}>
                      {formatValue(stat.value, stat.format)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Probability Analysis */}
        <div 
          className="rounded-xl overflow-hidden"
          style={{ background: colors.card, border: `1px solid ${colors.border}` }}
        >
          <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
            <h3 className="font-semibold text-white">Probability Analysis</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                  <th className="text-left px-6 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Metric</th>
                  <th className="text-right px-6 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Value</th>
                </tr>
              </thead>
              <tbody>
                {probStats.map((stat) => (
                  <tr key={stat.label} style={{ borderBottom: `1px solid ${colors.border}` }} className="hover:bg-white/[0.02]">
                    <td className="px-6 py-3" style={{ color: colors.text }}>{stat.label}</td>
                    <td className="text-right px-6 py-3 font-mono" style={{
                      color: stat.label.includes('Positive') ? colors.emerald : colors.coral
                    }}>
                      {stat.value.toFixed(2)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Percentiles Table */}
      <div 
        className="rounded-xl overflow-hidden"
        style={{ background: colors.card, border: `1px solid ${colors.border}` }}
      >
        <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
          <h3 className="font-semibold text-white">Return Percentiles</h3>
          <p className="text-sm" style={{ color: colors.textMuted }}>Full distribution of returns at percentile levels</p>
        </div>
        <div className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Percentile</th>
                  {['1st', '5th', '10th', '25th', '50th', '75th', '90th', '95th', '99th'].map(p => (
                    <th key={p} className="text-center px-4 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>{p}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="font-medium px-4 py-3 text-white">Return</td>
                  {[stats.p1, stats.p5, stats.p10, stats.p25, stats.p50, stats.p75, stats.p90, stats.p95, stats.p99].map((p, i) => (
                    <td key={i} className="text-center font-mono px-4 py-3" style={{ color: p >= 0 ? colors.emerald : colors.coral }}>
                      {(p * 100).toFixed(2)}%
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Summary & Export */}
      <div 
        className="rounded-xl overflow-hidden"
        style={{ background: colors.card, border: `1px solid ${colors.border}` }}
      >
        <div className="px-6 py-4 flex items-center justify-between flex-wrap gap-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
          <div>
            <h3 className="font-semibold text-white">Portfolio Summary</h3>
            <p className="text-sm" style={{ color: colors.textMuted }}>Optimization method: {result.method}</p>
          </div>
          <div className="flex items-center gap-2">
            {/* Share Link */}
            <button
              onClick={handleCopyLink}
              className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium transition-all hover:bg-white/10"
              style={{ 
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: copySuccess ? colors.emerald : colors.text
              }}
              aria-label="Copy shareable link"
            >
              {copySuccess ? <CheckCircle className="w-4 h-4" /> : <Share2 className="w-4 h-4" />}
              {copySuccess ? 'Copied!' : 'Share'}
            </button>
            
            {/* Export Weights */}
            <button
              onClick={handleExportWeights}
              className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium transition-all hover:bg-white/10"
              style={{ 
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: colors.text
              }}
              aria-label="Export weights only"
            >
              <Copy className="w-4 h-4" />
              Weights
            </button>
            
            {/* Export JSON */}
            <button
              onClick={handleExportJSON}
              className="flex items-center gap-2 px-3 py-2 rounded-lg font-medium transition-all hover:bg-white/10"
              style={{ 
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: colors.text
              }}
              aria-label="Export as JSON"
            >
              <FileJson className="w-4 h-4" />
              JSON
            </button>
            
            {/* Export CSV (primary) */}
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all hover:opacity-90"
              style={{ 
                background: 'linear-gradient(135deg, #14B8A6 0%, #10B981 100%)', 
                color: 'white',
                boxShadow: '0 0 15px rgba(20,184,166,0.3)'
              }}
              aria-label="Export full report as CSV"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-4 gap-4">
            <div 
              className="rounded-xl p-4"
              style={{ 
                background: 'rgba(255,255,255,0.03)',
                border: `1px solid ${colors.border}`
              }}
            >
              <p className="text-sm mb-1" style={{ color: colors.textMuted }}>Total Scenarios</p>
              <p className="text-2xl font-bold text-white">{result.portfolio_returns.length.toLocaleString()}</p>
            </div>
            <div 
              className="rounded-xl p-4"
              style={{ 
                background: result.status === 'optimal' 
                  ? 'rgba(16,185,129,0.1)' 
                  : 'rgba(251,191,36,0.1)',
                border: `1px solid ${result.status === 'optimal' ? 'rgba(16,185,129,0.3)' : 'rgba(251,191,36,0.3)'}`
              }}
            >
              <p className="text-sm mb-1" style={{ color: colors.textMuted }}>Optimization Status</p>
              <div className="flex items-center gap-2">
                {result.status === 'optimal' ? (
                  <CheckCircle className="w-5 h-5" style={{ color: colors.emerald }} />
                ) : (
                  <XCircle className="w-5 h-5" style={{ color: '#FBBF24' }} />
                )}
                <p className="text-2xl font-bold" style={{ color: result.status === 'optimal' ? colors.emerald : '#FBBF24' }}>
                  {result.status === 'optimal' ? 'Optimal' : 'Suboptimal'}
                </p>
              </div>
            </div>
            <div 
              className="rounded-xl p-4"
              style={{ 
                background: 'rgba(34,211,238,0.1)',
                border: '1px solid rgba(34,211,238,0.3)'
              }}
            >
              <p className="text-sm mb-1" style={{ color: colors.textMuted }}>Number of Assets</p>
              <p className="text-2xl font-bold" style={{ color: colors.cyan }}>{Object.keys(result.weights).length}</p>
            </div>
            <div 
              className="rounded-xl p-4"
              style={{ 
                background: 'rgba(20,184,166,0.1)',
                border: '1px solid rgba(20,184,166,0.3)'
              }}
            >
              <p className="text-sm mb-1" style={{ color: colors.textMuted }}>Active Positions</p>
              <p className="text-2xl font-bold" style={{ color: colors.teal }}>
                {Object.values(result.weights).filter(w => w > 0.01).length}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
