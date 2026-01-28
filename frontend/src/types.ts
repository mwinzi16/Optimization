/**
 * @fileoverview Type definitions for the Portfolio Optimizer application.
 * 
 * This module contains all TypeScript interfaces and types used across the
 * frontend application for API communication and UI state management.
 * 
 * @module types
 * @author Portfolio Optimizer Team
 * @version 2.0.0
 */

// ============================================================================
// API Types - Data structures for backend communication
// ============================================================================

/**
 * Information about a single asset (ILS/Cat Bond) in the portfolio universe.
 * 
 * @interface AssetInfo
 * @property {string} name - Unique identifier for the asset (e.g., "CAT_BOND_001")
 * @property {number} expected_return - Annualized expected return (0.08 = 8%)
 * @property {number} no_loss_return - Return assuming no catastrophe event occurs
 * @property {number} expected_loss - Expected loss from catastrophe events
 * @property {number} volatility - Annualized standard deviation of returns
 * @property {number} var_90 - Value at Risk at 90% confidence (positive = loss)
 * @property {number} var_95 - Value at Risk at 95% confidence
 * @property {number} var_99 - Value at Risk at 99% confidence
 * @property {number} cvar_95 - Conditional VaR (Expected Shortfall) at 95%
 * 
 * @example
 * const asset: AssetInfo = {
 *   name: "Florida_Hurricane_2026",
 *   expected_return: 0.082,
 *   no_loss_return: 0.095,
 *   expected_loss: 0.013,
 *   volatility: 0.156,
 *   var_90: 0.05,
 *   var_95: 0.12,
 *   var_99: 0.35,
 *   cvar_95: 0.234
 * };
 */
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

/**
 * Request payload for portfolio optimization.
 * 
 * Different optimization methods require different parameters. The backend
 * will use sensible defaults for parameters not relevant to the selected method.
 * 
 * @interface OptimizationRequest
 * @property {string} method - Optimization method to use
 * @property {number} min_weight - Minimum weight per asset (0-1)
 * @property {number} max_weight - Maximum weight per asset (0-1)
 * @property {number} risk_free_rate - Annual risk-free rate for Sharpe calculation
 * @property {number} cvar_alpha - Confidence level for CVaR (0.9-0.99)
 * @property {number} risk_aversion - Trade-off parameter for Mean-CVaR (0=min risk, 1=max return)
 * @property {number} exp_risk_aversion - CARA risk aversion coefficient (higher = more risk averse)
 * @property {number} [max_volatility] - Maximum allowed portfolio volatility
 * @property {number} [max_cvar] - Maximum allowed portfolio CVaR
 * @property {string} constraint_type - Type of risk constraint ('volatility' | 'cvar')
 * @property {number} [cvar_constraint_alpha] - Confidence level for CVaR constraint
 * 
 * @example
 * // Maximum Sharpe Ratio optimization
 * const request: OptimizationRequest = {
 *   method: 'Maximum Sharpe Ratio',
 *   min_weight: 0.01,
 *   max_weight: 0.15,
 *   risk_free_rate: 0.02,
 *   cvar_alpha: 0.95,
 *   risk_aversion: 0.5,
 *   exp_risk_aversion: 2.0,
 *   constraint_type: 'volatility'
 * };
 */
export interface OptimizationRequest {
  method: string;
  min_weight: number;
  max_weight: number;
  risk_free_rate: number;
  cvar_alpha: number;
  risk_aversion: number;
  exp_risk_aversion: number;
  max_volatility?: number;
  max_cvar?: number;
  constraint_type: string;
  cvar_constraint_alpha?: number;
}

/**
 * Response from portfolio optimization containing weights and comprehensive metrics.
 * 
 * This response includes the optimal portfolio weights, risk/return metrics,
 * and detailed distribution statistics for scenario analysis.
 * 
 * @interface OptimizationResponse
 * @property {string} status - Optimization status ('success' or 'error')
 * @property {string} method - Method used for optimization
 * @property {Record<string, number>} weights - Asset name to weight mapping (sums to 1)
 * @property {object} metrics - Portfolio-level risk and return metrics
 * @property {number[]} portfolio_returns - Array of scenario-level returns
 * @property {object} distribution_stats - Detailed distribution statistics
 */
export interface OptimizationResponse {
  status: string;
  method: string;
  weights: Record<string, number>;
  metrics: {
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
    max_drawdown: number;
  };
  portfolio_returns: number[];
  distribution_stats: {
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
  };
  best_scenario_returns: Record<string, number>;  // Each asset's return in the best portfolio scenario
  var90_scenario_returns: Record<string, number>;  // Each asset's return in the VaR90 scenario
  var95_scenario_returns: Record<string, number>;  // Each asset's return in the VaR95 scenario
  var99_scenario_returns: Record<string, number>;  // Each asset's return in the VaR99 scenario
  asset_mean_returns: Record<string, number>;  // Mean return for each asset
}

/**
 * A single point on the efficient frontier.
 * 
 * The efficient frontier represents the set of optimal portfolios that offer
 * the highest expected return for a given level of risk. Each point represents
 * a different risk-return trade-off.
 * 
 * @interface EfficientFrontierPoint
 * @property {number} expected_return - Expected annual return at this point
 * @property {number} volatility - Portfolio volatility (standard deviation)
 * @property {number} sharpe_ratio - Risk-adjusted return (return - rf) / volatility
 * @property {number} cvar_95 - 95% Conditional Value at Risk
 * 
 * @example
 * const point: EfficientFrontierPoint = {
 *   expected_return: 0.08,
 *   volatility: 0.12,
 *   sharpe_ratio: 0.5,
 *   cvar_95: 0.15
 * };
 */
export interface EfficientFrontierPoint {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  cvar_95: number;
}

// ============================================================================
// UI Types - Types for frontend state management and UI logic
// ============================================================================

/**
 * Available portfolio optimization methods.
 * 
 * Each method uses a different objective function and approach:
 * - **Maximum Sharpe Ratio**: Maximizes risk-adjusted return
 * - **Minimum Variance**: Minimizes portfolio volatility
 * - **Minimum CVaR**: Minimizes tail risk (expected shortfall)
 * - **Mean-CVaR Trade-off**: Balances return and tail risk
 * - **Maximum Return (Constrained)**: Maximizes return with risk constraints
 * - **Exponential Utility (CARA)**: Uses CARA utility function for risk preferences
 * 
 * @typedef {string} OptimizationMethod
 */
export type OptimizationMethod = 
  | 'Maximum Sharpe Ratio'
  | 'Minimum Variance'
  | 'Minimum CVaR'
  | 'Mean-CVaR Trade-off'
  | 'Maximum Return (Constrained)'
  | 'Exponential Utility (CARA)';

/**
 * Available tabs in the main content area.
 * 
 * @typedef {'distribution' | 'allocation' | 'risk' | 'stats'} TabType
 * @description
 * - `distribution` - Return distribution analysis (histograms, scenarios)
 * - `allocation` - Portfolio allocation visualization (pie/bar charts)
 * - `risk` - Risk analysis with efficient frontier
 * - `stats` - Comprehensive statistics and export options
 */
export type TabType = 'distribution' | 'allocation' | 'risk' | 'stats';
