export const CHART_COLORS = [
  '#10B981', // emerald
  '#14B8A6', // teal
  '#3B82F6', // blue
  '#FBBF24', // amber
  '#F87171', // red
  '#8B5CF6', // violet
  '#EC4899', // pink
  '#06B6D4', // cyan
  '#F59E0B', // yellow
  '#6366F1', // indigo
  '#84CC16', // lime
  '#EF4444', // red-500
  '#22D3EE', // cyan-400
  '#A78BFA', // violet-400
  '#FB923C', // orange-400
] as const;

export const METRIC_CARD_VARIANTS = {
  positive: 'linear-gradient(135deg, #059669, #047857)',
  negative: 'linear-gradient(135deg, #dc2626, #b91c1c)',
  neutral: 'linear-gradient(135deg, #0d9488, #0f766e)',
  warning: 'linear-gradient(135deg, #d97706, #b45309)',
} as const;