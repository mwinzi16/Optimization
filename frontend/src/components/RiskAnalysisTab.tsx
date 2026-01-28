import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  ScatterChart,
  Scatter,
} from 'recharts';
import { OptimizationResponse, EfficientFrontierPoint } from '../types';

interface RiskAnalysisTabProps {
  result: OptimizationResponse;
  frontier: EfficientFrontierPoint[];
}

// Dark theme colors
const colors = {
  card: 'rgba(255,255,255,0.02)',
  border: 'rgba(255,255,255,0.06)',
  grid: 'rgba(255,255,255,0.06)',
  text: '#a1a1aa',
  textMuted: '#71717a',
  white: '#e4e4e7',
  teal: '#14B8A6',
  emerald: '#10B981',
  gold: '#FBBF24',
  coral: '#F87171',
  cyan: '#22D3EE',
  violet: '#A78BFA',
};

export default function RiskAnalysisTab({ result, frontier }: RiskAnalysisTabProps) {
  const stats = result.distribution_stats;
  
  // Prepare efficient frontier data
  const frontierData = frontier.map(p => ({
    volatility: p.volatility * 100,
    return: p.expected_return * 100,
    sharpe: p.sharpe_ratio,
    cvar: p.cvar_95 * 100,
  }));

  // Current portfolio point
  const currentPortfolio = {
    volatility: result.metrics.volatility * 100,
    return: result.metrics.expected_return * 100,
  };

  // Loss probability data
  const probData = [
    { name: 'Positive Return', probability: stats.prob_positive * 100, color: colors.emerald },
    { name: 'Loss > 5%', probability: stats.prob_loss_5 * 100, color: colors.gold },
    { name: 'Loss > 10%', probability: stats.prob_loss_10 * 100, color: '#F59E0B' },
    { name: 'Loss > 25%', probability: stats.prob_loss_25 * 100, color: colors.coral },
    { name: 'Loss > 50%', probability: stats.prob_loss_50 * 100, color: '#DC2626' },
  ];

  // Risk gauge data
  const gauges = [
    { label: 'Volatility', value: result.metrics.volatility * 100, max: 30, thresholds: [10, 20] },
    { label: 'VaR 95% (Loss)', value: -result.metrics.var_95 * 100, max: 50, thresholds: [15, 30] },
    { label: 'CVaR 95% (Loss)', value: -result.metrics.cvar_95 * 100, max: 50, thresholds: [20, 35] },
    { label: 'Max Loss', value: -result.metrics.max_drawdown * 100, max: 100, thresholds: [30, 60] },
  ];

  const getGaugeColor = (value: number, thresholds: number[]) => {
    if (value <= thresholds[0]) return colors.emerald;
    if (value <= thresholds[1]) return colors.gold;
    return colors.coral;
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        {/* Efficient Frontier */}
        <div 
          className="rounded-xl overflow-hidden"
          style={{ background: colors.card, border: `1px solid ${colors.border}` }}
        >
          <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
            <h3 className="font-semibold text-white">Efficient Frontier</h3>
            <p className="text-sm" style={{ color: colors.textMuted }}>Risk-return trade-off with optimal portfolio position</p>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={350}>
              <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                <XAxis
                  type="number"
                  dataKey="volatility"
                  name="Volatility"
                  domain={['dataMin - 1', 'dataMax + 1']}
                  tickFormatter={(v) => `${v.toFixed(0)}%`}
                  tick={{ fontSize: 12, fill: colors.text }}
                  axisLine={{ stroke: colors.border }}
                  label={{ value: 'Volatility (%)', position: 'bottom', offset: 0, fill: colors.textMuted }}
                />
                <YAxis
                  type="number"
                  dataKey="return"
                  name="Return"
                  domain={['dataMin - 0.5', 'dataMax + 0.5']}
                  tickFormatter={(v) => `${v.toFixed(1)}%`}
                  tick={{ fontSize: 12, fill: colors.text }}
                  axisLine={{ stroke: colors.border }}
                  label={{ value: 'Expected Return (%)', angle: -90, position: 'insideLeft', fill: colors.textMuted }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length > 0) {
                      const data = payload[0].payload;
                      return (
                        <div style={{ 
                          background: '#1a1a1c', 
                          border: `1px solid ${colors.teal}`,
                          borderRadius: 8,
                          padding: '8px 12px',
                          color: colors.white
                        }}>
                          <div style={{ fontSize: '12px', marginBottom: '4px' }}>
                            <span style={{ color: colors.textMuted }}>Volatility: </span>
                            <span style={{ fontWeight: 600 }}>{data.volatility.toFixed(2)}%</span>
                          </div>
                          <div style={{ fontSize: '12px' }}>
                            <span style={{ color: colors.textMuted }}>Expected Return: </span>
                            <span style={{ fontWeight: 600 }}>{data.return.toFixed(2)}%</span>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                
                {/* Frontier line */}
                <Scatter
                  name="Efficient Frontier"
                  data={frontierData}
                  line={{ stroke: colors.cyan, strokeWidth: 2 }}
                  fill={colors.cyan}
                  shape="circle"
                />
                
                {/* Current portfolio */}
                <Scatter
                  name="Optimal Portfolio"
                  data={[currentPortfolio]}
                  fill={colors.emerald}
                  shape="star"
                >
                  <Cell fill={colors.emerald} />
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Loss Probability */}
        <div 
          className="rounded-xl overflow-hidden"
          style={{ background: colors.card, border: `1px solid ${colors.border}` }}
        >
          <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
            <h3 className="font-semibold text-white">Loss Probability Analysis</h3>
            <p className="text-sm" style={{ color: colors.textMuted }}>Probability of exceeding various loss thresholds</p>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={probData} layout="vertical" margin={{ top: 20, right: 30, left: 100, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                <XAxis
                  type="number"
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                  tick={{ fontSize: 12, fill: colors.text }}
                  axisLine={{ stroke: colors.border }}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 12, fill: colors.text }}
                  axisLine={{ stroke: colors.border }}
                  width={90}
                />
                <Tooltip
                  formatter={(value: number) => [`${value.toFixed(2)}%`, 'Probability']}
                  contentStyle={{ 
                    background: '#1a1a1c', 
                    border: `1px solid ${colors.teal}`,
                    borderRadius: 8,
                    color: colors.white
                  }}
                />
                <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                  {probData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Risk Gauges */}
      <div 
        className="rounded-xl overflow-hidden"
        style={{ background: colors.card, border: `1px solid ${colors.border}` }}
      >
        <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
          <h3 className="font-semibold text-white">Risk Gauges</h3>
          <p className="text-sm" style={{ color: colors.textMuted }}>Visual indicators for key risk metrics</p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-4 gap-6">
            {gauges.map((gauge) => (
              <div key={gauge.label} className="text-center">
                <div 
                  className="relative h-3 rounded-full overflow-hidden mb-3"
                  style={{ background: 'rgba(255,255,255,0.1)' }}
                >
                  {/* Threshold markers */}
                  <div
                    className="absolute h-full w-px z-10"
                    style={{ left: `${(gauge.thresholds[0] / gauge.max) * 100}%`, background: 'rgba(255,255,255,0.3)' }}
                  />
                  <div
                    className="absolute h-full w-px z-10"
                    style={{ left: `${(gauge.thresholds[1] / gauge.max) * 100}%`, background: 'rgba(255,255,255,0.3)' }}
                  />
                  {/* Value bar */}
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min((gauge.value / gauge.max) * 100, 100)}%`,
                      backgroundColor: getGaugeColor(gauge.value, gauge.thresholds),
                      boxShadow: `0 0 10px ${getGaugeColor(gauge.value, gauge.thresholds)}50`
                    }}
                  />
                </div>
                <p className="text-2xl font-bold" style={{ color: getGaugeColor(gauge.value, gauge.thresholds) }}>
                  {gauge.value.toFixed(1)}%
                </p>
                <p className="text-sm" style={{ color: colors.textMuted }}>{gauge.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Percentile Distribution */}
      <div 
        className="rounded-xl overflow-hidden"
        style={{ background: colors.card, border: `1px solid ${colors.border}` }}
      >
        <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
          <h3 className="font-semibold text-white">Return Percentiles</h3>
          <p className="text-sm" style={{ color: colors.textMuted }}>Distribution of returns at key percentile levels</p>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-9 gap-2 text-center">
            {[
              { label: '1st', value: stats.p1 },
              { label: '5th', value: stats.p5 },
              { label: '10th', value: stats.p10 },
              { label: '25th', value: stats.p25 },
              { label: '50th', value: stats.p50 },
              { label: '75th', value: stats.p75 },
              { label: '90th', value: stats.p90 },
              { label: '95th', value: stats.p95 },
              { label: '99th', value: stats.p99 },
            ].map((p) => (
              <div
                key={p.label}
                className="p-3 rounded-lg transition-all hover:scale-105"
                style={{ 
                  background: p.value >= 0 
                    ? 'rgba(16,185,129,0.15)' 
                    : 'rgba(248,113,113,0.15)',
                  border: `1px solid ${p.value >= 0 ? 'rgba(16,185,129,0.3)' : 'rgba(248,113,113,0.3)'}`
                }}
              >
                <p className="text-xs mb-1" style={{ color: colors.textMuted }}>{p.label}</p>
                <p className="font-bold" style={{ color: p.value >= 0 ? colors.emerald : colors.coral }}>
                  {(p.value * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
