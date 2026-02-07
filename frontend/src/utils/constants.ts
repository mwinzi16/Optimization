import type { MethodInfo, OptimizationMethod, TabType } from '../types';

export const METHODS: OptimizationMethod[] = [
  'Maximum Sharpe Ratio',
  'Minimum Variance',
  'Minimum CVaR',
  'Mean-CVaR Trade-off',
  'Maximum Return (Constrained)',
  'Exponential Utility (CARA)',
];

export const METHOD_INFO: Record<OptimizationMethod, MethodInfo> = {
  'Maximum Sharpe Ratio': {
    goal: 'Find the portfolio with the highest risk-adjusted return.',
    description:
      'Maximizes the ratio of excess return (above risk-free rate) to volatility. Finds the tangency portfolio on the efficient frontier — the optimal trade-off between risk and return.',
    formula: 'SR = (E[Rₚ] − Rᶠ) / σₚ',
    bestFor: 'Investors seeking the most efficient risk-return trade-off.',
  },
  'Minimum Variance': {
    goal: 'Find the portfolio with the lowest possible volatility.',
    description:
      'Minimizes portfolio standard deviation through diversification. Leverages low-correlation assets to reduce overall risk, often underweighting high-return but volatile assets.',
    formula: 'min √(wᵀΣw)',
    bestFor: 'Conservative investors prioritizing stability over returns.',
  },
  'Minimum CVaR': {
    goal: 'Minimize expected losses in worst-case scenarios.',
    description:
      'Minimizes Conditional Value at Risk (Expected Shortfall) — the average loss in the worst α% of scenarios. Uses the Rockafellar-Uryasev linear programming formulation for efficient convex optimization.',
    formula: 'min CVaRα = E[L | L > VaRα]',
    bestFor: 'Risk-averse investors focused on tail-risk protection.',
  },
  'Mean-CVaR Trade-off': {
    goal: 'Balance expected return against tail risk.',
    description:
      'Optimizes a weighted combination: min(−E[R] + λ·CVaR). The risk aversion parameter λ controls the trade-off — low λ favors return, high λ penalizes tail risk.',
    formula: 'min −E[R] + λ · CVaRα',
    bestFor: 'Investors who want explicit control over risk-return preferences.',
  },
  'Maximum Return (Constrained)': {
    goal: 'Maximize expected return within a risk budget.',
    description:
      'Finds the highest-return portfolio subject to a volatility or CVaR constraint. Useful when risk limits are externally imposed by regulation, mandates, or investment policy.',
    formula: 'max E[R] s.t. σ ≤ σₘₐₓ or CVaR ≤ CVaRₘₐₓ',
    bestFor: 'Portfolio managers with regulatory or mandate-driven risk limits.',
  },
  'Exponential Utility (CARA)': {
    goal: 'Optimize using a theoretically grounded risk-aversion model.',
    description:
      'Maximizes expected exponential (CARA) utility: U(W) = −e^(−c·W). Higher c penalizes downside more heavily. Based on Constant Absolute Risk Aversion theory from Elton/Gruber\'s Modern Portfolio Theory.',
    formula: 'max E[U] = E[−e^(−c · 50 · R)]',
    bestFor: 'Quantitative investors with well-defined risk preferences.',
  },
};

export const TABS: { key: TabType; label: string; icon: string }[] = [
  { key: 'distribution', label: 'Distribution', icon: 'BarChart3' },
  { key: 'allocation', label: 'Allocation', icon: 'PieChart' },
  { key: 'risk', label: 'Risk Analysis', icon: 'TrendingDown' },
  { key: 'stats', label: 'Statistics', icon: 'Table' },
];