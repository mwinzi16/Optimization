import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  AreaChart,
  Area,
  LineChart,
  Line,
} from 'recharts';
import { OptimizationResponse } from '../types';

interface DistributionTabProps {
  result: OptimizationResponse;
}

// Dark theme colors
const colors = {
  background: '#111113',
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
};

export default function DistributionTab({ result }: DistributionTabProps) {
  // Create histogram data
  const returns = result.portfolio_returns;
  const min = Math.min(...returns);
  const max = Math.max(...returns);
  const nBins = 50;
  const binWidth = (max - min) / nBins;
  
  const histogramData: { bin: number; count: number; label: string }[] = [];
  for (let i = 0; i < nBins; i++) {
    const binStart = min + i * binWidth;
    const binEnd = binStart + binWidth;
    const count = returns.filter(r => r >= binStart && r < binEnd).length;
    histogramData.push({
      bin: binStart,
      count,
      label: `${(binStart * 100).toFixed(1)}% to ${(binEnd * 100).toFixed(1)}%`,
    });
  }

  // Create CDF data with years (1/probability) on x-axis
  const sortedReturns = [...returns].sort((a, b) => a - b);
  const nScenarios = sortedReturns.length;
  
  const cdfData = sortedReturns
    .map((r, i) => {
      const rank = i + 1;
      const exceedanceProbability = rank / nScenarios;
      const returnPeriodYears = nScenarios / rank;
      return {
        returnPct: r * 100,
        years: returnPeriodYears,
        probability: exceedanceProbability * 100,
      };
    })
    .filter((_, i, arr) => {
      // Always include first (min) and last (max) points
      if (i === 0 || i === arr.length - 1) return true;
      if (i < 100) return i % 1 === 0;
      if (i < 500) return i % 5 === 0;
      if (i < 2000) return i % 20 === 0;
      return i % 100 === 0;
    })
    .reverse();

  // Scenario returns (sample for performance)
  const sampleSize = 500;
  const step = Math.floor(returns.length / sampleSize);
  const scenarioData = returns
    .filter((_, i) => i % step === 0)
    .map((r, i) => ({
      scenario: i * step + 1,
      return: r * 100,
    }));

  const { var_95, cvar_95 } = result.metrics;
  const meanReturn = result.distribution_stats.mean;

  return (
    <div className="space-y-6">
      {/* Return Period Chart - Full Width */}
      <div 
        className="rounded-xl overflow-hidden"
        style={{ background: colors.card, border: `1px solid ${colors.border}` }}
      >
        <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
          <h3 className="font-semibold text-white">Return vs Return Period (Years)</h3>
          <p className="text-sm" style={{ color: colors.textMuted }}>Expected return at different return periods (log scale)</p>
        </div>
        <div className="p-6">
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={cdfData} margin={{ top: 30, right: 30, left: 20, bottom: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
              <XAxis
                dataKey="years"
                scale="log"
                domain={[1, 10000]}
                type="number"
                tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v.toFixed(0)}
                ticks={[1, 10, 100, 1000, 10000]}
                tick={{ fontSize: 12, fill: colors.text }}
                axisLine={{ stroke: colors.border }}
                label={{ value: 'Return Period (Years)', position: 'bottom', offset: 10, fill: colors.textMuted }}
              />
              <YAxis
                dataKey="returnPct"
                tickFormatter={(v) => `${v.toFixed(0)}%`}
                tick={{ fontSize: 12, fill: colors.text }}
                axisLine={{ stroke: colors.border }}
                label={{ value: 'Return (%)', angle: -90, position: 'insideLeft', fill: colors.textMuted }}
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
                        <div style={{ fontSize: '12px', marginBottom: '4px', fontWeight: 600 }}>
                          1-in-{Math.round(data.years)} year event
                        </div>
                        <div style={{ fontSize: '12px', marginBottom: '2px' }}>
                          <span style={{ color: colors.textMuted }}>Return Period: </span>
                          <span>{data.years >= 1000 ? `${(data.years/1000).toFixed(1)}k` : data.years.toFixed(0)} years</span>
                        </div>
                        <div style={{ fontSize: '12px' }}>
                          <span style={{ color: colors.textMuted }}>Return: </span>
                          <span style={{ color: data.returnPct >= 0 ? colors.emerald : colors.coral }}>{data.returnPct.toFixed(2)}%</span>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Area
                type="monotone"
                dataKey="returnPct"
                stroke={colors.teal}
                fill="url(#cdfGradientDark)"
                strokeWidth={2}
              />
              <defs>
                <linearGradient id="cdfGradientDark" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={colors.teal} stopOpacity={0.4} />
                  <stop offset="95%" stopColor={colors.teal} stopOpacity={0.05} />
                </linearGradient>
              </defs>
              
              <ReferenceLine x={10} stroke={colors.text} strokeWidth={1} strokeDasharray="3 3" label={{ value: '1-in-10', position: 'top', fill: colors.text, fontSize: 10 }} />
              <ReferenceLine x={20} stroke={colors.text} strokeWidth={1} strokeDasharray="3 3" label={{ value: '1-in-20', position: 'top', fill: colors.text, fontSize: 10 }} />
              <ReferenceLine x={50} stroke={colors.text} strokeWidth={1} strokeDasharray="3 3" label={{ value: '1-in-50', position: 'top', fill: colors.text, fontSize: 10 }} />
              <ReferenceLine x={100} stroke={colors.gold} strokeWidth={2} strokeDasharray="5 5" label={{ value: '1-in-100', position: 'top', fill: colors.gold, fontSize: 11, fontWeight: 600 }} />
              <ReferenceLine x={250} stroke={colors.coral} strokeWidth={2} strokeDasharray="5 5" label={{ value: '1-in-250', position: 'top', fill: colors.coral, fontSize: 11, fontWeight: 600 }} />
              <ReferenceLine x={500} stroke={colors.coral} strokeWidth={1} strokeDasharray="3 3" label={{ value: '1-in-500', position: 'top', fill: colors.coral, fontSize: 10 }} />
              <ReferenceLine y={0} stroke={colors.textMuted} strokeDasharray="3 3" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Histogram */}
        <div 
          className="rounded-xl overflow-hidden"
          style={{ background: colors.card, border: `1px solid ${colors.border}` }}
        >
          <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
            <h3 className="font-semibold text-white">Portfolio Return Distribution</h3>
            <p className="text-sm" style={{ color: colors.textMuted }}>Distribution of returns across 10,000 scenarios</p>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={histogramData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                <XAxis
                  dataKey="bin"
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  tick={{ fontSize: 11, fill: colors.text }}
                  axisLine={{ stroke: colors.border }}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: colors.text }}
                  axisLine={{ stroke: colors.border }}
                />
                <Tooltip
                  formatter={(value: number) => [value, 'Count']}
                  labelFormatter={(v) => `Return: ${(v * 100).toFixed(1)}%`}
                  contentStyle={{ 
                    background: '#1a1a1c', 
                    border: `1px solid ${colors.emerald}`,
                    borderRadius: 8,
                    color: colors.white
                  }}
                />
                <Bar dataKey="count" fill={colors.emerald} radius={[2, 2, 0, 0]} />
                
                <ReferenceLine
                  x={var_95}
                  stroke={colors.gold}
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  label={{ value: `VaR 95%`, position: 'top', fill: colors.gold, fontSize: 10, fontWeight: 600 }}
                />
                
                <ReferenceLine
                  x={cvar_95}
                  stroke={colors.coral}
                  strokeWidth={2}
                  strokeDasharray="3 3"
                  label={{ value: `CVaR 95%`, position: 'top', fill: colors.coral, fontSize: 10, fontWeight: 600 }}
                />
                
                <ReferenceLine
                  x={meanReturn}
                  stroke={colors.teal}
                  strokeWidth={2}
                  label={{ value: `Mean`, position: 'top', fill: colors.teal, fontSize: 10, fontWeight: 600 }}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Scenario Returns */}
        <div 
          className="rounded-xl overflow-hidden"
          style={{ background: colors.card, border: `1px solid ${colors.border}` }}
        >
          <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
            <h3 className="font-semibold text-white">Scenario Returns</h3>
            <p className="text-sm" style={{ color: colors.textMuted }}>Portfolio returns across sampled scenarios</p>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={scenarioData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
                <XAxis
                  dataKey="scenario"
                  tick={{ fontSize: 11, fill: colors.text }}
                  axisLine={{ stroke: colors.border }}
                  label={{ value: 'Scenario', position: 'bottom', offset: 0, fill: colors.textMuted }}
                />
                <YAxis
                  tickFormatter={(v) => `${v.toFixed(0)}%`}
                  tick={{ fontSize: 11, fill: colors.text }}
                  axisLine={{ stroke: colors.border }}
                  label={{ value: 'Return (%)', angle: -90, position: 'insideLeft', fill: colors.textMuted }}
                />
                <Tooltip
                  formatter={(value: number) => [`${value.toFixed(2)}%`, 'Return']}
                  labelFormatter={(v) => `Scenario ${v}`}
                  contentStyle={{ 
                    background: '#1a1a1c', 
                    border: `1px solid ${colors.cyan}`,
                    borderRadius: 8,
                    color: colors.white
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="return"
                  stroke={colors.cyan}
                  strokeWidth={1}
                  dot={false}
                />
                <ReferenceLine y={0} stroke={colors.textMuted} strokeDasharray="3 3" />
                <ReferenceLine y={-25} stroke={colors.gold} strokeDasharray="3 3" label={{ value: '-25%', fill: colors.gold, fontSize: 10 }} />
                <ReferenceLine y={-50} stroke={colors.coral} strokeDasharray="3 3" label={{ value: '-50%', fill: colors.coral, fontSize: 10 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
