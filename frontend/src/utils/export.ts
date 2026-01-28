/**
 * @fileoverview Export utilities for portfolio optimization results.
 * 
 * This module provides functions for exporting portfolio data to various
 * formats (CSV, JSON) and for generating shareable URLs.
 * 
 * Features:
 * - Full portfolio export to CSV with all metrics
 * - Portfolio weights export (simple CSV)
 * - JSON export for programmatic use
 * - Shareable URL generation with base64 encoding
 * - Clipboard copy functionality
 * 
 * @module utils/export
 * @author Portfolio Optimizer Team
 * @version 2.0.0
 * 
 * @example
 * import { exportToCSV, exportWeightsToCSV, generateShareableURL } from './export';
 * 
 * // Export full results to CSV
 * exportToCSV(optimizationResult, config);
 * 
 * // Export just the weights
 * exportWeightsToCSV(optimizationResult.weights);
 * 
 * // Generate a shareable URL
 * const url = generateShareableURL(config);
 * await copyToClipboard(url);
 */

import { OptimizationResponse, OptimizationMethod } from '../types';

/**
 * Configuration parameters for portfolio optimization.
 * Used for including settings in exports and generating shareable URLs.
 */
interface ExportConfig {
  /** Optimization method used */
  method: OptimizationMethod;
  /** Risk-free rate (0.02 = 2%) */
  riskFreeRate: number;
  /** Minimum weight per asset (0.01 = 1%) */
  minWeight: number;
  /** Maximum weight per asset (0.15 = 15%) */
  maxWeight: number;
  /** CVaR confidence level (95 = 95%) */
  cvarAlpha: number;
  /** Mean-CVaR trade-off parameter */
  riskAversion: number;
  /** CARA exponential risk aversion */
  expRiskAversion: number;
  /** Type of risk constraint for max return method */
  constraintType: 'volatility' | 'cvar';
  /** Maximum volatility constraint (10 = 10%) */
  maxVolatility: number;
  /** Maximum CVaR constraint (15 = 15%) */
  maxCvar: number;
}

/**
 * Format a number for export with consistent decimal places.
 * 
 * @param value - The number to format
 * @param decimals - Number of decimal places (default: 4)
 * @returns Formatted string representation
 */
function formatNumber(value: number, decimals: number = 4): string {
  return value.toFixed(decimals);
}

/**
 * Generate a formatted date string for filenames.
 * Format: YYYYMMDD_HHMM (e.g., 20260127_1430)
 * 
 * @returns Formatted date string
 */
function getFormattedDate(): string {
  const now = new Date();
  return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
}

/**
 * Export complete optimization results to a CSV file.
 * 
 * Generates a comprehensive CSV containing:
 * - Configuration parameters
 * - Portfolio metrics (return, volatility, Sharpe, VaR, CVaR)
 * - Distribution statistics (skewness, kurtosis, percentiles)
 * - Probability analysis
 * - Portfolio weights for each asset
 * 
 * @param result - The optimization result to export
 * @param config - Optional configuration parameters to include
 * 
 * @example
 * exportToCSV(result, {
 *   method: 'Maximum Sharpe Ratio',
 *   riskFreeRate: 0.02,
 *   minWeight: 1,
 *   maxWeight: 15,
 *   // ... other config
 * });
 */
export function exportToCSV(result: OptimizationResponse, config?: ExportConfig): void {
  const lines: string[] = [];
  
  // Header
  lines.push('ILS Portfolio Optimization Results');
  lines.push(`Generated: ${new Date().toISOString()}`);
  lines.push(`Optimization Method: ${result.method}`);
  lines.push(`Status: ${result.status}`);
  lines.push('');
  
  // Configuration (if provided)
  if (config) {
    lines.push('=== Configuration ===');
    lines.push(`Risk-Free Rate,${(config.riskFreeRate).toFixed(2)}%`);
    lines.push(`Min Weight,${config.minWeight}%`);
    lines.push(`Max Weight,${config.maxWeight}%`);
    lines.push(`CVaR Alpha,${config.cvarAlpha}%`);
    if (config.method === 'Mean-CVaR Trade-off') {
      lines.push(`Risk Aversion,${config.riskAversion}`);
    }
    if (config.method === 'Exponential Utility (CARA)') {
      lines.push(`Exp Risk Aversion,${config.expRiskAversion}`);
    }
    if (config.method === 'Maximum Return (Constrained)') {
      lines.push(`Constraint Type,${config.constraintType}`);
      if (config.constraintType === 'volatility') {
        lines.push(`Max Volatility,${config.maxVolatility}%`);
      } else {
        lines.push(`Max CVaR,${config.maxCvar}%`);
      }
    }
    lines.push('');
  }
  
  // Portfolio Metrics
  lines.push('=== Portfolio Metrics ===');
  lines.push('Metric,Value');
  lines.push(`Expected Return,${formatNumber(result.metrics.expected_return * 100)}%`);
  lines.push(`Volatility,${formatNumber(result.metrics.volatility * 100)}%`);
  lines.push(`Sharpe Ratio,${formatNumber(result.metrics.sharpe_ratio)}`);
  lines.push(`VaR 90%,${formatNumber(result.metrics.var_90 * 100)}%`);
  lines.push(`VaR 95%,${formatNumber(result.metrics.var_95 * 100)}%`);
  lines.push(`VaR 98%,${formatNumber(result.metrics.var_98 * 100)}%`);
  lines.push(`VaR 99%,${formatNumber(result.metrics.var_99 * 100)}%`);
  lines.push(`CVaR 90%,${formatNumber(result.metrics.cvar_90 * 100)}%`);
  lines.push(`CVaR 95%,${formatNumber(result.metrics.cvar_95 * 100)}%`);
  lines.push(`CVaR 98%,${formatNumber(result.metrics.cvar_98 * 100)}%`);
  lines.push(`CVaR 99%,${formatNumber(result.metrics.cvar_99 * 100)}%`);
  lines.push(`Max Drawdown,${formatNumber(result.metrics.max_drawdown * 100)}%`);
  lines.push('');
  
  // Distribution Stats
  lines.push('=== Distribution Statistics ===');
  lines.push('Metric,Value');
  lines.push(`Mean,${formatNumber(result.distribution_stats.mean * 100)}%`);
  lines.push(`Median,${formatNumber(result.distribution_stats.median * 100)}%`);
  lines.push(`Standard Deviation,${formatNumber(result.distribution_stats.std * 100)}%`);
  lines.push(`Skewness,${formatNumber(result.distribution_stats.skewness)}`);
  lines.push(`Kurtosis,${formatNumber(result.distribution_stats.kurtosis)}`);
  lines.push(`No-Loss Return,${formatNumber(result.distribution_stats.no_loss_return * 100)}%`);
  lines.push(`Expected Loss,${formatNumber(result.distribution_stats.expected_loss * 100)}%`);
  lines.push(`Min,${formatNumber(result.distribution_stats.min * 100)}%`);
  lines.push(`Max,${formatNumber(result.distribution_stats.max * 100)}%`);
  lines.push('');
  
  // Probability Analysis
  lines.push('=== Probability Analysis ===');
  lines.push('Metric,Value');
  lines.push(`Prob(Return > 0),${formatNumber(result.distribution_stats.prob_positive * 100)}%`);
  lines.push(`Prob(Loss > 5%),${formatNumber(result.distribution_stats.prob_loss_5 * 100)}%`);
  lines.push(`Prob(Loss > 10%),${formatNumber(result.distribution_stats.prob_loss_10 * 100)}%`);
  lines.push(`Prob(Loss > 25%),${formatNumber(result.distribution_stats.prob_loss_25 * 100)}%`);
  lines.push(`Prob(Loss > 50%),${formatNumber(result.distribution_stats.prob_loss_50 * 100)}%`);
  lines.push('');
  
  // Percentiles
  lines.push('=== Return Percentiles ===');
  lines.push('Percentile,Return');
  lines.push(`1st,${formatNumber(result.distribution_stats.p1 * 100)}%`);
  lines.push(`5th,${formatNumber(result.distribution_stats.p5 * 100)}%`);
  lines.push(`10th,${formatNumber(result.distribution_stats.p10 * 100)}%`);
  lines.push(`25th,${formatNumber(result.distribution_stats.p25 * 100)}%`);
  lines.push(`50th (Median),${formatNumber(result.distribution_stats.p50 * 100)}%`);
  lines.push(`75th,${formatNumber(result.distribution_stats.p75 * 100)}%`);
  lines.push(`90th,${formatNumber(result.distribution_stats.p90 * 100)}%`);
  lines.push(`95th,${formatNumber(result.distribution_stats.p95 * 100)}%`);
  lines.push(`99th,${formatNumber(result.distribution_stats.p99 * 100)}%`);
  lines.push('');
  
  // Portfolio Weights
  lines.push('=== Portfolio Weights ===');
  lines.push('Asset,Weight');
  Object.entries(result.weights)
    .sort(([, a], [, b]) => b - a)
    .forEach(([name, weight]) => {
      lines.push(`${name},${formatNumber(weight * 100, 4)}%`);
    });
  
  // Create and download file
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ils_portfolio_${getFormattedDate()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Export just portfolio weights to CSV.
 */
export function exportWeightsToCSV(weights: Record<string, number>): void {
  const lines: string[] = [];
  
  lines.push('Asset,Weight,Weight (%)');
  Object.entries(weights)
    .sort(([, a], [, b]) => b - a)
    .forEach(([name, weight]) => {
      lines.push(`${name},${formatNumber(weight, 6)},${formatNumber(weight * 100, 4)}%`);
    });
  
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `portfolio_weights_${getFormattedDate()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Generate shareable URL with optimization parameters.
 */
export function generateShareableURL(config: ExportConfig): string {
  const params = new URLSearchParams();
  
  params.set('method', config.method);
  params.set('rfr', config.riskFreeRate.toString());
  params.set('minW', config.minWeight.toString());
  params.set('maxW', config.maxWeight.toString());
  params.set('cvarA', config.cvarAlpha.toString());
  params.set('ra', config.riskAversion.toString());
  params.set('era', config.expRiskAversion.toString());
  params.set('ct', config.constraintType);
  params.set('maxVol', config.maxVolatility.toString());
  params.set('maxCvar', config.maxCvar.toString());
  
  const baseUrl = window.location.origin + window.location.pathname;
  return `${baseUrl}?${params.toString()}`;
}

/**
 * Parse URL parameters to get optimization config.
 */
export function parseShareableURL(): Partial<ExportConfig> | null {
  const params = new URLSearchParams(window.location.search);
  
  if (params.size === 0) return null;
  
  return {
    method: (params.get('method') as OptimizationMethod) || undefined,
    riskFreeRate: params.has('rfr') ? parseFloat(params.get('rfr')!) : undefined,
    minWeight: params.has('minW') ? parseFloat(params.get('minW')!) : undefined,
    maxWeight: params.has('maxW') ? parseFloat(params.get('maxW')!) : undefined,
    cvarAlpha: params.has('cvarA') ? parseFloat(params.get('cvarA')!) : undefined,
    riskAversion: params.has('ra') ? parseFloat(params.get('ra')!) : undefined,
    expRiskAversion: params.has('era') ? parseFloat(params.get('era')!) : undefined,
    constraintType: (params.get('ct') as 'volatility' | 'cvar') || undefined,
    maxVolatility: params.has('maxVol') ? parseFloat(params.get('maxVol')!) : undefined,
    maxCvar: params.has('maxCvar') ? parseFloat(params.get('maxCvar')!) : undefined,
  };
}

/**
 * Copy text to clipboard with fallback.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    } else {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.left = '-999999px';
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    }
  } catch {
    return false;
  }
}

/**
 * Export data as JSON for programmatic use.
 */
export function exportToJSON(result: OptimizationResponse, config?: ExportConfig): void {
  const data = {
    exportDate: new Date().toISOString(),
    config: config || null,
    result: {
      status: result.status,
      method: result.method,
      metrics: result.metrics,
      distributionStats: result.distribution_stats,
      weights: result.weights,
    },
  };
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ils_portfolio_${getFormattedDate()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
