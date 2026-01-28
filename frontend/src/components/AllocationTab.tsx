import { useState, useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import { OptimizationResponse, AssetInfo } from '../types';

interface AllocationTabProps {
  result: OptimizationResponse;
  assets: AssetInfo[];
}

// Extended color palette for many assets
const COLORS = [
  '#14B8A6', '#10B981', '#22D3EE', '#FBBF24', '#F87171', '#A78BFA', '#34D399', '#60A5FA',
  '#FB923C', '#4ADE80', '#38BDF8', '#E879F9', '#FACC15', '#2DD4BF', '#818CF8', '#F472B6',
  '#84CC16', '#06B6D4', '#8B5CF6', '#EC4899', '#EAB308', '#0EA5E9', '#7C3AED', '#DB2777',
];

const colors = {
  card: 'rgba(255,255,255,0.02)',
  border: 'rgba(255,255,255,0.06)',
  grid: 'rgba(255,255,255,0.06)',
  text: '#a1a1aa',
  textMuted: '#71717a',
  white: '#e4e4e7',
  teal: '#14B8A6',
  emerald: '#10B981',
  coral: '#F87171',
};

type ContributionType = 'noLossReturn' | 'expectedLoss' | 'var90' | 'var95' | 'var99';

const contributionOptions: { id: ContributionType; label: string }[] = [
  { id: 'noLossReturn', label: 'No-Loss Return' },
  { id: 'expectedLoss', label: 'Expected Loss' },
  { id: 'var90', label: 'VaR 90%' },
  { id: 'var95', label: 'VaR 95%' },
  { id: 'var99', label: 'VaR 99%' },
];

const TOP_N_CHART = 15; // Show top N assets in charts, group rest as "Other"
const PAGE_SIZE = 50; // Number of rows per page in table

export default function AllocationTab({ result, assets }: AllocationTabProps) {
  const [selectedContribution, setSelectedContribution] = useState<ContributionType>('noLossReturn');
  const [currentPage, setCurrentPage] = useState(0);
  const [showAllInTable, setShowAllInTable] = useState(false);
  const weights = result.weights;
  
  // Portfolio-level metrics (contributions = weight × portfolio metric)
  const portfolioNoLossReturn = result.distribution_stats.no_loss_return;
  const portfolioExpectedLoss = result.distribution_stats.expected_loss;
  const portfolioVar90 = result.metrics.var_90;
  const portfolioVar95 = result.metrics.var_95;
  const portfolioVar99 = result.metrics.var_99;
  
  // Prepare table data with asset info - memoized for performance
  const tableData = useMemo(() => {
    return Object.entries(weights).map(([name, weight]) => {
      const assetInfo = assets.find(a => a.name === name);
      
      return {
        name,
        weight: weight * 100,
        // Asset's own metrics (for display)
        noLossReturn: (assetInfo ? assetInfo.no_loss_return : 0) * 100,
        expectedLoss: (assetInfo ? assetInfo.expected_loss : 0) * 100,
        expectedReturn: (assetInfo ? assetInfo.expected_return : 0) * 100,
        var90: (assetInfo ? assetInfo.var_90 : 0) * 100,
        var95: (assetInfo ? assetInfo.var_95 : 0) * 100,
        var99: (assetInfo ? assetInfo.var_99 : 0) * 100,
        // Contributions = weight × portfolio metric (so they sum to portfolio total)
        noLossReturnContribution: weight * portfolioNoLossReturn * 100,
        expectedLossContribution: weight * portfolioExpectedLoss * 100,
        var90Contribution: weight * portfolioVar90 * 100,
        var95Contribution: weight * portfolioVar95 * 100,
        var99Contribution: weight * portfolioVar99 * 100,
      };
    }).sort((a, b) => b.weight - a.weight);
  }, [weights, assets, portfolioNoLossReturn, portfolioExpectedLoss, portfolioVar90, portfolioVar95, portfolioVar99]);

  const totalAssets = tableData.length;
  const hasManySssets = totalAssets > 20;

  // Prepare pie chart data - group small allocations for large portfolios
  const allocationChartData = useMemo(() => {
    const significant = tableData.filter(row => row.weight > 0.1);
    
    if (significant.length <= TOP_N_CHART) {
      return significant.map(row => ({ name: row.name, value: row.weight }));
    }
    
    // Take top N, group rest as "Other"
    const topN = significant.slice(0, TOP_N_CHART);
    const otherWeight = significant.slice(TOP_N_CHART).reduce((sum, row) => sum + row.weight, 0);
    
    const data = topN.map(row => ({ name: row.name, value: row.weight }));
    if (otherWeight > 0.01) {
      data.push({ name: `Other (${significant.length - TOP_N_CHART})`, value: otherWeight });
    }
    return data;
  }, [tableData]);

  // Prepare contribution chart data
  const contributionChartData = useMemo(() => {
    const getData = (contribution: ContributionType) => {
      return tableData.map(row => {
        let actualValue = 0;
        switch (contribution) {
          case 'noLossReturn': actualValue = row.noLossReturnContribution; break;
          case 'expectedLoss': actualValue = row.expectedLossContribution; break;
          case 'var90': actualValue = row.var90Contribution; break;
          case 'var95': actualValue = row.var95Contribution; break;
          case 'var99': actualValue = row.var99Contribution; break;
        }
        return { name: row.name, value: Math.abs(actualValue), actualValue };
      }).filter(item => item.value > 0.001).sort((a, b) => b.value - a.value);
    };
    
    const data = getData(selectedContribution);
    
    if (data.length <= TOP_N_CHART) return data;
    
    // Group smaller contributions
    const topN = data.slice(0, TOP_N_CHART);
    const otherValue = data.slice(TOP_N_CHART).reduce((sum, item) => sum + item.actualValue, 0);
    
    if (Math.abs(otherValue) > 0.001) {
      topN.push({ name: `Other (${data.length - TOP_N_CHART})`, value: Math.abs(otherValue), actualValue: otherValue });
    }
    return topN;
  }, [tableData, selectedContribution]);

  const totalContribution = useMemo(() => {
    return tableData.reduce((sum, row) => {
      switch (selectedContribution) {
        case 'noLossReturn': return sum + row.noLossReturnContribution;
        case 'expectedLoss': return sum + row.expectedLossContribution;
        case 'var90': return sum + row.var90Contribution;
        case 'var95': return sum + row.var95Contribution;
        case 'var99': return sum + row.var99Contribution;
      }
    }, 0);
  }, [tableData, selectedContribution]);
  
  const getMetricLabel = () => {
    switch (selectedContribution) {
      case 'noLossReturn': return 'Portfolio No-Loss Return';
      case 'expectedLoss': return 'Portfolio Expected Loss';
      case 'var90': return 'Portfolio VaR 90%';
      case 'var95': return 'Portfolio VaR 95%';
      case 'var99': return 'Portfolio VaR 99%';
    }
  };

  // Pagination for table
  const paginatedData = useMemo(() => {
    if (showAllInTable) return tableData;
    const start = currentPage * PAGE_SIZE;
    return tableData.slice(start, start + PAGE_SIZE);
  }, [tableData, currentPage, showAllInTable]);

  const totalPages = Math.ceil(tableData.length / PAGE_SIZE);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        {/* Allocation Chart */}
        <div 
          className="rounded-xl overflow-hidden"
          style={{ background: colors.card, border: `1px solid ${colors.border}` }}
        >
          <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
            <h3 className="font-semibold text-white">Portfolio Allocation</h3>
            <p className="text-sm" style={{ color: colors.textMuted }}>
              {totalAssets} assets{hasManySssets && ` (top ${Math.min(TOP_N_CHART, allocationChartData.length)} shown)`}
            </p>
          </div>
          <div className="p-6">
            {hasManySssets ? (
              // Bar chart for many assets
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={allocationChartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} horizontal={false} />
                  <XAxis type="number" tick={{ fill: colors.text, fontSize: 10 }} tickFormatter={(v) => `${v.toFixed(1)}%`} />
                  <YAxis 
                    type="category" 
                    dataKey="name" 
                    tick={{ fill: colors.text, fontSize: 10 }} 
                    width={100}
                    tickFormatter={(v) => v.length > 12 ? v.substring(0, 12) + '...' : v}
                  />
                  <Tooltip
                    formatter={(value: number) => [`${value.toFixed(2)}%`, 'Weight']}
                    contentStyle={{ background: '#1a1a1c', border: `1px solid ${colors.teal}`, borderRadius: 8, color: colors.white }}
                  />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {allocationChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              // Pie chart for fewer assets
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={allocationChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={110}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, value }) => `${name.substring(0, 10)}: ${value.toFixed(1)}%`}
                    labelLine={{ stroke: colors.textMuted, strokeWidth: 1 }}
                  >
                    {allocationChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => [`${value.toFixed(2)}%`, 'Weight']}
                    contentStyle={{ background: '#1a1a1c', border: `1px solid ${colors.teal}`, borderRadius: 8, color: colors.white }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Contribution Chart */}
        <div 
          className="rounded-xl overflow-hidden"
          style={{ background: colors.card, border: `1px solid ${colors.border}` }}
        >
          <div className="px-6 py-4" style={{ borderBottom: `1px solid ${colors.border}` }}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-white">Contribution Analysis</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {contributionOptions.map(option => (
                <button
                  key={option.id}
                  onClick={() => setSelectedContribution(option.id)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                  style={{
                    background: selectedContribution === option.id 
                      ? 'linear-gradient(135deg, rgba(20,184,166,0.3) 0%, rgba(16,185,129,0.3) 100%)'
                      : 'rgba(255,255,255,0.04)',
                    border: selectedContribution === option.id 
                      ? '1px solid rgba(20,184,166,0.5)'
                      : '1px solid rgba(255,255,255,0.08)',
                    color: selectedContribution === option.id ? '#5eead4' : '#71717a'
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={contributionChartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} horizontal={false} />
                <XAxis type="number" tick={{ fill: colors.text, fontSize: 10 }} tickFormatter={(v) => `${v.toFixed(2)}%`} />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  tick={{ fill: colors.text, fontSize: 10 }} 
                  width={100}
                  tickFormatter={(v) => v.length > 12 ? v.substring(0, 12) + '...' : v}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length > 0) {
                      const data = payload[0].payload as { name: string; actualValue: number };
                      return (
                        <div style={{ background: '#1a1a1c', border: `1px solid ${colors.teal}`, borderRadius: 8, padding: '8px 12px', color: colors.white }}>
                          <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>{data.name}</div>
                          <div style={{ fontSize: '12px' }}>
                            <span style={{ color: colors.textMuted }}>Contribution: </span>
                            <span style={{ fontWeight: 600, color: data.actualValue >= 0 ? colors.emerald : colors.coral }}>{data.actualValue.toFixed(3)}%</span>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {contributionChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.actualValue >= 0 ? colors.emerald : colors.coral} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="text-center mt-2 space-y-1">
              <div className="text-xs" style={{ color: colors.textMuted }}>{getMetricLabel()}</div>
              <span className="text-lg font-semibold" style={{ color: totalContribution >= 0 ? colors.emerald : colors.coral }}>
                {totalContribution.toFixed(3)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Weights Table */}
      <div 
        className="rounded-xl overflow-hidden"
        style={{ background: colors.card, border: `1px solid ${colors.border}` }}
      >
        <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: `1px solid ${colors.border}` }}>
          <div>
            <h3 className="font-semibold text-white">Portfolio Weights & Contributions</h3>
            <p className="text-sm" style={{ color: colors.textMuted }}>
              {totalAssets} assets • Showing {paginatedData.length} of {tableData.length}
            </p>
          </div>
          {totalAssets > PAGE_SIZE && (
            <button
              onClick={() => setShowAllInTable(!showAllInTable)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.08)',
                color: colors.teal
              }}
            >
              {showAllInTable ? 'Paginate' : 'Show All'}
            </button>
          )}
        </div>
        <div className="overflow-x-auto" style={{ maxHeight: showAllInTable ? '600px' : 'auto', overflowY: showAllInTable ? 'auto' : 'visible' }}>
          <table className="w-full text-sm">
            <thead className="sticky top-0" style={{ background: '#111113' }}>
              <tr style={{ borderBottom: `1px solid ${colors.border}` }}>
                <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Asset</th>
                <th className="text-right px-3 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Weight</th>
                <th className="text-right px-3 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>No-Loss Ret.</th>
                <th className="text-right px-3 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Exp. Loss</th>
                <th className="text-right px-3 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.textMuted }}>Exp. Return</th>
                <th className="text-right px-3 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.teal }}>NLR Contrib.</th>
                <th className="text-right px-4 py-3 text-xs font-medium uppercase tracking-wider" style={{ color: colors.coral }}>EL Contrib.</th>
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((row, i) => (
                <tr 
                  key={row.name}
                  style={{ borderBottom: `1px solid ${colors.border}` }}
                  className="hover:bg-white/[0.02] transition-colors"
                >
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: COLORS[(currentPage * PAGE_SIZE + i) % COLORS.length] }}
                      />
                      <span className="font-medium text-white text-xs" title={row.name}>
                        {row.name.length > 25 ? row.name.substring(0, 25) + '...' : row.name}
                      </span>
                    </div>
                  </td>
                  <td className="text-right px-3 py-2 font-mono text-xs" style={{ color: colors.text }}>{row.weight.toFixed(2)}%</td>
                  <td className="text-right px-3 py-2 font-mono text-xs" style={{ color: colors.emerald }}>{row.noLossReturn.toFixed(2)}%</td>
                  <td className="text-right px-3 py-2 font-mono text-xs" style={{ color: colors.coral }}>{row.expectedLoss.toFixed(2)}%</td>
                  <td className="text-right px-3 py-2 font-mono text-xs" style={{ color: row.expectedReturn >= 0 ? colors.emerald : colors.coral }}>{row.expectedReturn.toFixed(2)}%</td>
                  <td className="text-right px-3 py-2 font-mono font-semibold text-xs" style={{ color: colors.teal }}>{row.noLossReturnContribution.toFixed(3)}%</td>
                  <td className="text-right px-4 py-2 font-mono font-semibold text-xs" style={{ color: colors.coral }}>{row.expectedLossContribution.toFixed(3)}%</td>
                </tr>
              ))}
            </tbody>
            <tfoot className="sticky bottom-0" style={{ background: '#111113' }}>
              <tr style={{ background: 'rgba(255,255,255,0.02)' }}>
                <td className="px-4 py-3 font-semibold text-white text-xs">Total</td>
                <td className="text-right px-3 py-3 font-mono font-semibold text-white text-xs">
                  {tableData.reduce((sum, r) => sum + r.weight, 0).toFixed(2)}%
                </td>
                <td className="text-right px-3 py-3" style={{ color: colors.textMuted }}>-</td>
                <td className="text-right px-3 py-3" style={{ color: colors.textMuted }}>-</td>
                <td className="text-right px-3 py-3" style={{ color: colors.textMuted }}>-</td>
                <td className="text-right px-3 py-3 font-mono font-semibold text-xs" style={{ color: colors.teal }}>
                  {tableData.reduce((sum, r) => sum + r.noLossReturnContribution, 0).toFixed(3)}%
                </td>
                <td className="text-right px-4 py-3 font-mono font-semibold text-xs" style={{ color: colors.coral }}>
                  {tableData.reduce((sum, r) => sum + r.expectedLossContribution, 0).toFixed(3)}%
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
        
        {/* Pagination */}
        {!showAllInTable && totalPages > 1 && (
          <div className="px-6 py-3 flex items-center justify-between" style={{ borderTop: `1px solid ${colors.border}` }}>
            <span className="text-xs" style={{ color: colors.textMuted }}>
              Page {currentPage + 1} of {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(0, p - 1))}
                disabled={currentPage === 0}
                className="px-3 py-1.5 rounded text-xs font-medium transition-all disabled:opacity-40"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: colors.text }}
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={currentPage >= totalPages - 1}
                className="px-3 py-1.5 rounded text-xs font-medium transition-all disabled:opacity-40"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: colors.text }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
