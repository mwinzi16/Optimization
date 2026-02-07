import { useMemo, useState } from 'react';
import { Table, Copy, Check } from 'lucide-react';
import { useOptimizationStore } from '../stores/optimizationStore';
import { formatPercent } from '../utils/format';
import { useUiStore } from '../stores/uiStore';

export function StatsTab() {
  const { result } = useOptimizationStore();
  const { addToast } = useUiStore();
  const [copied, setCopied] = useState(false);

  const percentiles = useMemo(() => {
    if (!result) return [];
    const s = result.distribution_stats;
    return [
      { label: '1st', value: s.p1 },
      { label: '5th', value: s.p5 },
      { label: '10th', value: s.p10 },
      { label: '25th', value: s.p25 },
      { label: '50th (Median)', value: s.p50 },
      { label: '75th', value: s.p75 },
      { label: '90th', value: s.p90 },
      { label: '95th', value: s.p95 },
      { label: '99th', value: s.p99 },
    ];
  }, [result]);

  const scenarioTables = useMemo(() => {
    if (!result) return [];
    return [
      { title: 'Best Scenario Returns', data: result.best_scenario_returns },
      { title: 'VaR 90% Scenario Returns', data: result.var90_scenario_returns },
      { title: 'VaR 95% Scenario Returns', data: result.var95_scenario_returns },
      { title: 'VaR 99% Scenario Returns', data: result.var99_scenario_returns },
    ];
  }, [result]);

  const assetNames = useMemo(() => {
    if (!result) return [];
    return Object.keys(result.best_scenario_returns);
  }, [result]);

  const handleExport = () => {
    if (!result) return;

    const lines: string[] = [];

    // Percentiles
    lines.push('Percentile,Value');
    percentiles.forEach((p) => lines.push(`${p.label},${(p.value * 100).toFixed(4)}%`));
    lines.push('');

    // Distribution stats
    const s = result.distribution_stats;
    lines.push('Statistic,Value');
    lines.push(`Mean,${(s.mean * 100).toFixed(4)}%`);
    lines.push(`Median,${(s.median * 100).toFixed(4)}%`);
    lines.push(`Std Dev,${(s.std * 100).toFixed(4)}%`);
    lines.push(`Skewness,${s.skewness.toFixed(4)}`);
    lines.push(`Kurtosis,${s.kurtosis.toFixed(4)}`);
    lines.push('');

    // Scenario returns
    scenarioTables.forEach(({ title, data }) => {
      lines.push(title);
      lines.push('Asset,Return');
      Object.entries(data).forEach(([name, val]) =>
        lines.push(`${name},${(val * 100).toFixed(4)}%`),
      );
      lines.push('');
    });

    navigator.clipboard.writeText(lines.join('\n'));
    setCopied(true);
    addToast({ type: 'success', message: 'Statistics copied to clipboard as CSV.' });
    setTimeout(() => setCopied(false), 2000);
  };

  if (!result) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-3 text-text-muted">
        <Table size={48} className="opacity-40" />
        <p className="text-lg font-medium">No Statistics Available</p>
        <p className="text-sm">
          Run an optimization to see detailed statistics and scenario analysis.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Export Button */}
      <div className="flex justify-end">
        <button
          onClick={handleExport}
          className="inline-flex items-center gap-2 rounded-lg bg-bg-elevated px-3 py-2 text-xs font-medium text-text-secondary border border-border-base hover:text-text-primary hover:border-border-light transition-colors"
        >
          {copied ? <Check size={14} className="text-accent-green" /> : <Copy size={14} />}
          {copied ? 'Copied!' : 'Export CSV'}
        </button>
      </div>

      {/* Percentile Table */}
      <div className="card overflow-hidden">
        <div className="border-b border-border-base px-4 py-3 lg:px-6">
          <h3 className="text-sm font-semibold text-text-primary">
            Return Percentiles
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border-base bg-bg-elevated">
                <th className="px-4 py-2.5 font-medium text-text-secondary">
                  Percentile
                </th>
                <th className="px-4 py-2.5 font-medium text-text-secondary text-right">
                  Value
                </th>
              </tr>
            </thead>
            <tbody>
              {percentiles.map((p, i) => (
                <tr
                  key={p.label}
                  className={`border-b border-border-base transition-colors hover:bg-bg-elevated/50 ${
                    i % 2 === 1 ? 'bg-bg-elevated/30' : ''
                  }`}
                >
                  <td className="px-4 py-2 text-text-primary">{p.label}</td>
                  <td
                    className={`px-4 py-2 text-right font-mono ${
                      p.value < 0 ? 'text-accent-coral' : 'text-accent-green'
                    }`}
                  >
                    {formatPercent(p.value)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scenario Analysis Tables */}
      {scenarioTables.map(({ title, data }) => (
        <div key={title} className="card overflow-hidden">
          <div className="border-b border-border-base px-4 py-3 lg:px-6">
            <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border-base bg-bg-elevated">
                  <th className="px-4 py-2.5 font-medium text-text-secondary">
                    Asset
                  </th>
                  <th className="px-4 py-2.5 font-medium text-text-secondary text-right">
                    Return
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(data).map(([name, val], i) => (
                  <tr
                    key={name}
                    className={`border-b border-border-base transition-colors hover:bg-bg-elevated/50 ${
                      i % 2 === 1 ? 'bg-bg-elevated/30' : ''
                    }`}
                  >
                    <td className="px-4 py-2 text-text-primary">{name}</td>
                    <td
                      className={`px-4 py-2 text-right font-mono ${
                        val < 0 ? 'text-accent-coral' : 'text-accent-green'
                      }`}
                    >
                      {formatPercent(val)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
