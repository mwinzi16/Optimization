import { useMemo } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  ReferenceLine,
} from 'recharts';
import { TrendingDown } from 'lucide-react';
import { useOptimizationStore } from '../stores/optimizationStore';
import { formatPercent } from '../utils/format';
import { CHART_COLORS } from '../utils/colors';
import { Skeleton } from './Skeleton';

export function RiskAnalysisTab() {
  const { result, frontier, isFrontierLoading } = useOptimizationStore();

  const frontierData = useMemo(
    () =>
      frontier.map((p) => ({
        volatility: p.volatility * 100,
        expected_return: p.expected_return * 100,
        sharpe_ratio: p.sharpe_ratio,
      })),
    [frontier],
  );

  const currentPortfolio = useMemo(() => {
    if (!result) return null;
    return {
      volatility: result.metrics.volatility * 100,
      expected_return: result.metrics.expected_return * 100,
      sharpe_ratio: result.metrics.sharpe_ratio,
    };
  }, [result]);

  const riskMetrics = useMemo(() => {
    if (!result) return [];
    const m = result.metrics;
    return [
      { label: 'VaR 90%', value: m.var_90 },
      { label: 'VaR 95%', value: m.var_95 },
      { label: 'VaR 98%', value: m.var_98 },
      { label: 'VaR 99%', value: m.var_99 },
      { label: 'CVaR 90%', value: m.cvar_90 },
      { label: 'CVaR 95%', value: m.cvar_95 },
      { label: 'CVaR 98%', value: m.cvar_98 },
      { label: 'CVaR 99%', value: m.cvar_99 },
      { label: 'Worst Scenario', value: m.worst_scenario },
    ];
  }, [result]);

  const lossProbData = useMemo(() => {
    if (!result) return [];
    const s = result.distribution_stats;
    return [
      { label: 'Loss > 5%', probability: s.prob_loss_5 * 100 },
      { label: 'Loss > 10%', probability: s.prob_loss_10 * 100 },
      { label: 'Loss > 25%', probability: s.prob_loss_25 * 100 },
      { label: 'Loss > 50%', probability: s.prob_loss_50 * 100 },
    ];
  }, [result]);

  if (!result) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-3 text-text-muted">
        <TrendingDown size={48} className="opacity-40" />
        <p className="text-lg font-medium">No Risk Data</p>
        <p className="text-sm">
          Run an optimization to see risk analysis and efficient frontier.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Efficient Frontier */}
      <div className="card p-4 lg:p-6">
        <h3 className="mb-4 text-sm font-semibold text-text-primary">
          Efficient Frontier
        </h3>
        {isFrontierLoading ? (
          <Skeleton variant="chart" />
        ) : frontierData.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-sm text-text-muted">
            No frontier data available. Run optimization to generate.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 10, right: 30, bottom: 20, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis
                type="number"
                dataKey="volatility"
                name="Volatility"
                tickFormatter={(v: number) => `${v.toFixed(1)}%`}
                tick={{ fill: '#a1a1aa', fontSize: 11 }}
                axisLine={{ stroke: '#27272a' }}
                label={{
                  value: 'Volatility (%)',
                  position: 'insideBottom',
                  offset: -10,
                  fill: '#71717a',
                  fontSize: 12,
                }}
              />
              <YAxis
                type="number"
                dataKey="expected_return"
                name="Expected Return"
                tickFormatter={(v: number) => `${v.toFixed(1)}%`}
                tick={{ fill: '#a1a1aa', fontSize: 11 }}
                axisLine={{ stroke: '#27272a' }}
                label={{
                  value: 'Expected Return (%)',
                  angle: -90,
                  position: 'insideLeft',
                  offset: 5,
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
                formatter={(value: number, name: string) => [
                  `${value.toFixed(2)}%`,
                  name,
                ]}
              />
              {/* Frontier Line */}
              <Scatter
                name="Frontier"
                data={frontierData}
                fill="#14B8A6"
                line={{ stroke: '#14B8A6', strokeWidth: 2 }}
                lineType="monotone"
                isAnimationActive={true}
              >
                {frontierData.map((_, idx) => (
                  <Cell key={idx} fill="#14B8A6" r={3} />
                ))}
              </Scatter>
              {/* Current Portfolio */}
              {currentPortfolio && (
                <Scatter
                  name="Current Portfolio"
                  data={[currentPortfolio]}
                  fill="#FBBF24"
                  isAnimationActive={false}
                >
                  <Cell fill="#FBBF24" r={8} />
                </Scatter>
              )}
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Risk Metrics Table */}
        <div className="card overflow-hidden">
          <div className="border-b border-border-base px-4 py-3 lg:px-6">
            <h3 className="text-sm font-semibold text-text-primary">Risk Metrics</h3>
          </div>
          <div className="p-4 lg:px-6">
            <div className="space-y-1">
              {riskMetrics.map((m) => (
                <div
                  key={m.label}
                  className="flex items-center justify-between border-b border-border-base py-2"
                >
                  <span className="text-xs text-text-muted">{m.label}</span>
                  <span
                    className={`text-xs font-medium font-mono ${
                      m.value < 0 ? 'text-accent-coral' : 'text-text-primary'
                    }`}
                  >
                    {formatPercent(m.value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Loss Probability Analysis */}
        <div className="card p-4 lg:p-6">
          <h3 className="mb-4 text-sm font-semibold text-text-primary">
            Loss Probability Analysis
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={lossProbData} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
              <XAxis
                type="number"
                tickFormatter={(v: number) => `${v.toFixed(1)}%`}
                tick={{ fill: '#a1a1aa', fontSize: 11 }}
                axisLine={{ stroke: '#27272a' }}
                domain={[0, 'auto']}
              />
              <YAxis
                type="category"
                dataKey="label"
                width={80}
                tick={{ fill: '#a1a1aa', fontSize: 11 }}
                axisLine={{ stroke: '#27272a' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#18181b',
                  border: '1px solid #27272a',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                formatter={(value: number) => [`${value.toFixed(2)}%`, 'Probability']}
              />
              <Bar
                dataKey="probability"
                radius={[0, 4, 4, 0]}
                isAnimationActive={true}
              >
                {lossProbData.map((_, idx) => (
                  <Cell
                    key={idx}
                    fill={
                      ['#FBBF24', '#F59E0B', '#F87171', '#DC2626'][idx] ?? '#F87171'
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
