import { useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RPieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { PieChart, ArrowUpDown } from 'lucide-react';
import { useOptimizationStore } from '../stores/optimizationStore';
import { useDataStore } from '../stores/dataStore';
import { CHART_COLORS } from '../utils/colors';
import { formatPercent } from '../utils/format';

type SortField = 'name' | 'weight' | 'expected_return' | 'volatility' | 'cvar_95';
type SortDir = 'asc' | 'desc';

export function AllocationTab() {
  const { result } = useOptimizationStore();
  const { assets } = useDataStore();
  const [sortField, setSortField] = useState<SortField>('weight');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const sortedWeights = useMemo(() => {
    if (!result) return [];
    return Object.entries(result.weights)
      .map(([name, weight]) => ({ name, weight }))
      .sort((a, b) => b.weight - a.weight);
  }, [result]);

  const pieData = useMemo(
    () => sortedWeights.filter((w) => w.weight > 0.001),
    [sortedWeights],
  );

  const barData = useMemo(
    () =>
      sortedWeights
        .filter((w) => w.weight > 0.0001)
        .map((w) => ({ ...w, weightPct: w.weight * 100 })),
    [sortedWeights],
  );

  const holdingsData = useMemo(() => {
    if (!result) return [];
    const assetMap = new Map(assets.map((a) => [a.name, a]));
    return Object.entries(result.weights).map(([name, weight]) => {
      const asset = assetMap.get(name);
      return {
        name,
        weight,
        expected_return: asset?.expected_return ?? 0,
        volatility: asset?.volatility ?? 0,
        cvar_95: asset?.cvar_95 ?? 0,
      };
    });
  }, [result, assets]);

  const sortedHoldings = useMemo(() => {
    const copy = [...holdingsData];
    copy.sort((a, b) => {
      const av = a[sortField] as number | string;
      const bv = b[sortField] as number | string;
      if (typeof av === 'string' && typeof bv === 'string')
        return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortDir === 'asc'
        ? (av as number) - (bv as number)
        : (bv as number) - (av as number);
    });
    return copy;
  }, [holdingsData, sortField, sortDir]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  if (!result) {
    return (
      <div className="flex h-96 flex-col items-center justify-center gap-3 text-text-muted">
        <PieChart size={48} className="opacity-40" />
        <p className="text-lg font-medium">No Allocation Data</p>
        <p className="text-sm">
          Run an optimization to see portfolio allocation breakdown.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Pie Chart */}
        <div className="card p-4 lg:p-6">
          <h3 className="mb-4 text-sm font-semibold text-text-primary">
            Weight Distribution
          </h3>
          <ResponsiveContainer width="100%" height={320}>
            <RPieChart>
              <Pie
                data={pieData}
                dataKey="weight"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={110}
                paddingAngle={2}
                isAnimationActive={true}
              >
                {pieData.map((_, idx) => (
                  <Cell
                    key={idx}
                    fill={CHART_COLORS[idx % CHART_COLORS.length]}
                    stroke="transparent"
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#18181b',
                  border: '1px solid #27272a',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                formatter={(value: number) => [formatPercent(value), 'Weight']}
              />
              <Legend
                wrapperStyle={{ fontSize: '11px', color: '#a1a1aa' }}
                iconType="circle"
                iconSize={8}
              />
            </RPieChart>
          </ResponsiveContainer>
        </div>

        {/* Horizontal Bar Chart */}
        <div className="card p-4 lg:p-6">
          <h3 className="mb-4 text-sm font-semibold text-text-primary">
            Asset Weights
          </h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={barData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
              <XAxis
                type="number"
                tickFormatter={(v: number) => `${v.toFixed(0)}%`}
                tick={{ fill: '#a1a1aa', fontSize: 11 }}
                axisLine={{ stroke: '#27272a' }}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={100}
                tick={{ fill: '#a1a1aa', fontSize: 10 }}
                axisLine={{ stroke: '#27272a' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#18181b',
                  border: '1px solid #27272a',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                formatter={(value: number) => [`${value.toFixed(2)}%`, 'Weight']}
              />
              <Bar
                dataKey="weightPct"
                fill="#14B8A6"
                radius={[0, 4, 4, 0]}
                isAnimationActive={true}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="card overflow-hidden">
        <div className="border-b border-border-base px-4 py-3 lg:px-6">
          <h3 className="text-sm font-semibold text-text-primary">Holdings</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border-base bg-bg-elevated">
                {(
                  [
                    ['name', 'Asset'],
                    ['weight', 'Weight (%)'],
                    ['expected_return', 'Expected Return'],
                    ['volatility', 'Volatility'],
                    ['cvar_95', 'CVaR 95%'],
                  ] as [SortField, string][]
                ).map(([field, label]) => (
                  <th
                    key={field}
                    onClick={() => toggleSort(field)}
                    className="cursor-pointer px-4 py-2.5 font-medium text-text-secondary hover:text-text-primary transition-colors"
                  >
                    <span className="inline-flex items-center gap-1">
                      {label}
                      <ArrowUpDown
                        size={12}
                        className={
                          sortField === field
                            ? 'text-accent-teal'
                            : 'text-text-muted opacity-50'
                        }
                      />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedHoldings.map((h, i) => (
                <tr
                  key={h.name}
                  className={`border-b border-border-base transition-colors hover:bg-bg-elevated/50 ${
                    i % 2 === 1 ? 'bg-bg-elevated/30' : ''
                  }`}
                >
                  <td className="px-4 py-2 font-medium text-text-primary">{h.name}</td>
                  <td className="px-4 py-2 font-mono text-text-secondary">
                    {formatPercent(h.weight)}
                  </td>
                  <td className="px-4 py-2 font-mono text-text-secondary">
                    {formatPercent(h.expected_return)}
                  </td>
                  <td className="px-4 py-2 font-mono text-text-secondary">
                    {formatPercent(h.volatility)}
                  </td>
                  <td className="px-4 py-2 font-mono text-text-secondary">
                    {formatPercent(h.cvar_95)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
