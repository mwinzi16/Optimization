/**
 * @fileoverview MetricCard component for displaying portfolio metrics.
 * 
 * A visually rich card component that displays a single metric with:
 * - Color-coded styling based on metric type (positive/negative/neutral/warning)
 * - Trend icons to indicate direction
 * - Optional tooltip for metric explanation
 * - Accessible markup with ARIA attributes
 * 
 * @module components/MetricCard
 */

import { memo } from 'react';
import { TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';
import { Tooltip } from './Tooltip';

/**
 * Props for the MetricCard component.
 */
interface MetricCardProps {
  /** Display label for the metric (e.g., "Expected Return") */
  label: string;
  /** Numeric value of the metric */
  value: number;
  /** How to format the value: 'percent' (×100 with %) or 'decimal' */
  format: 'percent' | 'decimal';
  /** Visual styling type affecting colors and icons */
  type: 'positive' | 'negative' | 'neutral' | 'warning';
  /** Optional tooltip text explaining the metric */
  tooltip?: string;
  /** Decimal precision for display (default: 2) */
  precision?: number;
}

const typeStyles = {
  positive: {
    bg: 'linear-gradient(135deg, rgba(16,185,129,0.15) 0%, rgba(16,185,129,0.05) 100%)',
    border: 'rgba(16,185,129,0.3)',
    color: '#10B981',
    glow: '0 0 20px rgba(16,185,129,0.15)',
    Icon: TrendingUp,
  },
  negative: {
    bg: 'linear-gradient(135deg, rgba(248,113,113,0.15) 0%, rgba(248,113,113,0.05) 100%)',
    border: 'rgba(248,113,113,0.3)',
    color: '#F87171',
    glow: '0 0 20px rgba(248,113,113,0.15)',
    Icon: TrendingDown,
  },
  neutral: {
    bg: 'linear-gradient(135deg, rgba(34,211,238,0.15) 0%, rgba(34,211,238,0.05) 100%)',
    border: 'rgba(34,211,238,0.3)',
    color: '#22D3EE',
    glow: '0 0 20px rgba(34,211,238,0.15)',
    Icon: Minus,
  },
  warning: {
    bg: 'linear-gradient(135deg, rgba(251,191,36,0.15) 0%, rgba(251,191,36,0.05) 100%)',
    border: 'rgba(251,191,36,0.3)',
    color: '#FBBF24',
    glow: '0 0 20px rgba(251,191,36,0.15)',
    Icon: AlertTriangle,
  },
};

/**
 * Displays a single portfolio metric in a styled card.
 * 
 * Features:
 * - Gradient backgrounds based on metric type
 * - Trend indicators (up/down arrows)
 * - Optional tooltip with explanatory text
 * - ARIA attributes for accessibility
 * - Memoized for performance
 * 
 * @param props - Component properties
 * @returns Rendered metric card
 * 
 * @example
 * <MetricCard
 *   label="Expected Return"
 *   value={0.085}
 *   format="percent"
 *   type="positive"
 *   tooltip="The weighted average of possible returns"
 * />
 * // Renders: "Expected Return: 8.50%"
 */
const MetricCard = memo(function MetricCard({ 
  label, 
  value, 
  format, 
  type, 
  tooltip,
  precision = 2 
}: MetricCardProps) {
  /**
   * Format the numeric value for display.
   * @param v - The raw numeric value
   * @returns Formatted string (e.g., "8.50%" or "1.25")
   */
  const formatValue = (v: number) => {
    if (format === 'percent') {
      return `${(v * 100).toFixed(precision)}%`;
    }
    return v.toFixed(precision);
  };

  const style = typeStyles[type];
  const Icon = style.Icon;

  const card = (
    <div 
      className="rounded-xl p-4 transition-all duration-300 hover:scale-[1.02] focus-within:ring-2 focus-within:ring-teal-500 focus-within:ring-offset-2 focus-within:ring-offset-zinc-900"
      style={{ 
        background: style.bg,
        border: `1px solid ${style.border}`,
        boxShadow: style.glow,
      }}
      role="article"
      aria-label={`${label}: ${formatValue(value)}`}
      tabIndex={0}
    >
      <div className="flex items-start justify-between">
        <div>
          <p 
            className="text-2xl font-bold" 
            style={{ color: style.color }}
            aria-hidden="true"
          >
            {formatValue(value)}
          </p>
          <p className="text-xs mt-1 text-zinc-400">{label}</p>
        </div>
        <div 
          className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: `${style.color}20` }}
          aria-hidden="true"
        >
          <Icon className="w-4 h-4" style={{ color: style.color }} />
        </div>
      </div>
    </div>
  );

  if (tooltip) {
    return (
      <Tooltip content={tooltip} position="top">
        {card}
      </Tooltip>
    );
  }

  return card;
});

export default MetricCard;
