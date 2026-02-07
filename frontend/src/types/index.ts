export type OptimizationMethod =
  | 'Maximum Sharpe Ratio'
  | 'Minimum Variance'
  | 'Minimum CVaR'
  | 'Mean-CVaR Trade-off'
  | 'Maximum Return (Constrained)'
  | 'Exponential Utility (CARA)';

export type ConstraintType = 'volatility' | 'cvar';
export type TabType = 'distribution' | 'allocation' | 'risk' | 'stats';

export interface HealthResponse {
  status: string;
  version: string;
  data_loaded: boolean;
  data_shape: { scenarios: number; assets: number } | null;
}

export interface AssetInfo {
  name: string;
  expected_return: number;
  no_loss_return: number;
  expected_loss: number;
  volatility: number;
  var_90: number;
  var_95: number;
  var_99: number;
  cvar_95: number;
}

export interface OptimizationRequest {
  method: OptimizationMethod;
  min_weight: number;
  max_weight: number;
  risk_free_rate: number;
  cvar_alpha?: number;
  risk_aversion?: number;
  exp_risk_aversion?: number;
  max_volatility?: number;
  max_cvar?: number;
  constraint_type?: ConstraintType;
  cvar_constraint_alpha?: number;
}

export interface OptimizationMetrics {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  var_90: number;
  var_95: number;
  var_98: number;
  var_99: number;
  cvar_90: number;
  cvar_95: number;
  cvar_98: number;
  cvar_99: number;
  worst_scenario: number;
}

export interface DistributionStats {
  mean: number;
  median: number;
  std: number;
  skewness: number;
  kurtosis: number;
  min: number;
  max: number;
  expected_loss: number;
  no_loss_return: number;
  prob_positive: number;
  prob_loss_5: number;
  prob_loss_10: number;
  prob_loss_25: number;
  prob_loss_50: number;
  p1: number;
  p5: number;
  p10: number;
  p25: number;
  p50: number;
  p75: number;
  p90: number;
  p95: number;
  p99: number;
}

export interface OptimizationResponse {
  status: string;
  method: string;
  weights: Record<string, number>;
  metrics: OptimizationMetrics;
  portfolio_returns: number[];
  distribution_stats: DistributionStats;
  best_scenario_returns: Record<string, number>;
  var90_scenario_returns: Record<string, number>;
  var95_scenario_returns: Record<string, number>;
  var99_scenario_returns: Record<string, number>;
  asset_mean_returns: Record<string, number>;
}

export interface EfficientFrontierPoint {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  cvar_95: number;
}

export interface UploadResponse {
  status: string;
  n_assets: number;
  n_scenarios: number;
  asset_names: string[];
}

export interface ApiEnvelope<T> {
  data: T;
  meta: Record<string, unknown>;
  errors: Array<{ code: string; message: string; details?: unknown }>;
}

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

export interface MethodInfo {
  goal: string;
  description: string;
  formula: string;
  bestFor: string;
}