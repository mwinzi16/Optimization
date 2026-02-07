import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { useOptimizationStore } from '../stores/optimizationStore';
import { formatPercent, formatRatio } from '../utils/format';
import { METRIC_CARD_VARIANTS } from '../utils/colors';
import { MetricCard } from './MetricCard';
import { BarChart3 } from 'lucide-react';

function buildHistogramData(returns: number[], binCount = 40) {
  if (returns.length === 0) return [];
  const sorted = [...returns].sort((a, b) => a - b);
  const min = sorted[0];
  const max = sorted[sorted.length - 1];
  const binWidth = (max - min) / binCount;
  if (binWidth === 0) return [{ binCenter: min * 100, count: returns.length }];

  const bins = Array.from({ length: binCount }, (_, i) => ({
    binCenter: (min + binWidth * (i + 0.5)) * 100,
    binStart: min + binWidth * i,
    count: 0,
  }));

  for (const r of returns) {
    let idx = Math.floor((r - min) / binWidth);
    if (idx >= binCount) idx = binCount - 1;
    bins[idx].count++;
  }

  return bins;
}

export function DistributionTab() {
  const { result } = useOptimizationStore();

  const histogramData = useMemo(
    () => (result ? buildHistogramData(result.portfolio_returns) : []),
    [result],
  );

  if (!result) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-3 text-text-muted">
        <BarChart3 size={48} className="opacity-40" />
        <p className="text-lg font-medium">No Optimization Results</p>
        <p className="text-sm">
          Configure parameters and run an optimization to see the return distribution.
        </p>
      </div>
    );
  }

  const { metrics, distribution_stats: stats } = result;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Metric Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <MetricCard
          label="Expected Return"
          value={formatPercent(metrics.expected_return)}
          gradient={METRIC_CARD_VARIANTS.positive}
        />
        <MetricCard
          label="Volatility"
          value={formatPercent(metrics.volatility)}
          gradient={METRIC_CARD_VARIANTS.neutral}
        />
        <MetricCard
          label="Sharpe Ratio"
          value={formatRatio(metrics.sharpe_ratio)}
          gradient={METRIC_CARD_VARIANTS.positive}
        />
        <MetricCard
          label="CVaR 95%"
          value={formatPercent(metrics.cvar_95)}
          gradient={METRIC_CARD_VARIANTS.negative}
        />
        <MetricCard
          label="Worst Scenario"
          value={formatPercent(metrics.worst_scenario)}
          gradient={METRIC_CARD_VARIANTS.negative}
        />
        <MetricCard
          label="P(Loss)"
          value={formatPercent(1 - stats.prob_positive)}
          gradient={METRIC_CARD_VARIANTS.warning}
        />
      </div>

      {/* Histogram */}
      <div className="card p-4 lg:p-6">
        <h3 className="mb-4 text-sm font-semibold text-text-primary">
          Portfolio Return Distribution
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={histogramData} barCategoryGap={0}>
            <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
            <XAxis
              dataKey="binCenter"
              tickFormatter={(v: number) => `${v.toFixed(1)}%`}
              tick={{ fill: '#a1a1aa', fontSize: 11 }}
              axisLine={{ stroke: '#27272a' }}
              label={{
                value: 'Portfolio Return (%)',
                position: 'insideBottom',
                offset: -5,
                fill: '#71717a',
                fontSize: 12,
              }}
            />
            <YAxis
              tick={{ fill: '#a1a1aa', fontSize: 11 }}
              axisLine={{ stroke: '#27272a' }}
              label={{
                value: 'Frequency',
                angle: -90,
                position: 'insideLeft',
                fill: '#71717a',
                fontSize: 12,
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#18181b',
                border: '1px solid #27272a',
                borderRadius: '8px',
                fontSize: '12px',
              }}
              labelFormatter={(v: number) => `Return: ${v.toFixed(2)}%`}
              formatter={(value: number) => [value, 'Count']}
            />
            <ReferenceLine
              x={stats.mean * 100}
              stroke="#10B981"
              strokeDasharray="4 4"
              label={{ value: 'Mean', fill: '#10B981', fontSize: 10, position: 'top' }}
            />
            <ReferenceLine
              x={metrics.var_95 * 100}
              stroke="#FBBF24"
              strokeDasharray="4 4"
              label={{ value: 'VaR 95', fill: '#FBBF24', fontSize: 10, position: 'top' }}
            />
            <ReferenceLine
              x={metrics.var_99 * 100}
              stroke="#F87171"
              strokeDasharray="4 4"
              label={{ value: 'VaR 99', fill: '#F87171', fontSize: 10, position: 'top' }}
            />
            <Bar
              dataKey="count"
              fill="#14B8A6"
              radius={[2, 2, 0, 0]}
              isAnimationActive={true}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      <div className="card p-4 lg:p-6">
        <h3 className="mb-4 text-sm font-semibold text-text-primary">
          Summary Statistics
        </h3>
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 sm:grid-cols-3 lg:grid-cols-4">
          <StatRow label="Mean" value={formatPercent(stats.mean)} />
          <StatRow label="Median" value={formatPercent(stats.median)} />
          <StatRow label="Std Dev" value={formatPercent(stats.std)} />
          <StatRow label="Skewness" value={formatRatio(stats.skewness)} />
          <StatRow label="Kurtosis" value={formatRatio(stats.kurtosis)} />
          <StatRow label="Min" value={formatPercent(stats.min)} />
          <StatRow label="Max" value={formatPercent(stats.max)} />
          <StatRow
            label="P(Positive)"
            value={formatPercent(stats.prob_positive)}
          />
          <StatRow
            label="P(Loss > 5%)"
            value={formatPercent(stats.prob_loss_5)}
          />
          <StatRow
            label="P(Loss > 10%)"
            value={formatPercent(stats.prob_loss_10)}
          />
          <StatRow
            label="P(Loss > 25%)"
            value={formatPercent(stats.prob_loss_25)}
          />
          <StatRow
            label="P(Loss > 50%)"
            value={formatPercent(stats.prob_loss_50)}
          />
        </div>
      </div>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border-base py-1.5">
      <span className="text-xs text-text-muted">{label}</span>
      <span className="text-xs font-medium text-text-primary">{value}</span>
    </div>
  );
}
