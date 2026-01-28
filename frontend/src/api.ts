/**
 * @fileoverview API client for the Portfolio Optimizer backend.
 * 
 * This module provides typed functions for all backend API endpoints,
 * handling request/response serialization and error handling.
 * 
 * @module api
 * @author Portfolio Optimizer Team
 * @version 2.0.0
 * 
 * @example
 * import { fetchAssets, optimizePortfolio, checkHealth } from './api';
 * 
 * // Check API health
 * const isHealthy = await checkHealth();
 * 
 * // Fetch available assets
 * const assets = await fetchAssets();
 * 
 * // Run optimization
 * const result = await optimizePortfolio({
 *   method: 'Maximum Sharpe Ratio',
 *   min_weight: 0.01,
 *   max_weight: 0.15,
 *   risk_free_rate: 0.02,
 *   cvar_alpha: 0.95,
 *   risk_aversion: 0.5,
 *   exp_risk_aversion: 2.0,
 *   constraint_type: 'volatility'
 * });
 */

import { AssetInfo, OptimizationRequest, OptimizationResponse, EfficientFrontierPoint } from './types';

/**
 * Base URL for API requests.
 * Uses relative path for Vite proxy configuration.
 * @constant {string}
 */
const API_BASE = '/api';

/**
 * Fetches information about all available assets in the portfolio universe.
 * 
 * @async
 * @function fetchAssets
 * @returns {Promise<AssetInfo[]>} Array of asset information objects
 * @throws {Error} If the API request fails
 * 
 * @example
 * const assets = await fetchAssets();
 * console.log(`Loaded ${assets.length} assets`);
 * assets.forEach(a => console.log(`${a.name}: ${(a.expected_return * 100).toFixed(2)}% return`));
 */
export async function fetchAssets(): Promise<AssetInfo[]> {
  const response = await fetch(`${API_BASE}/assets`);
  if (!response.ok) throw new Error('Failed to fetch assets');
  return response.json();
}

/**
 * Runs portfolio optimization with the specified method and parameters.
 * 
 * This is the main optimization endpoint that computes optimal portfolio
 * weights based on the selected method and constraints.
 * 
 * @async
 * @function optimizePortfolio
 * @param {OptimizationRequest} request - Optimization parameters
 * @returns {Promise<OptimizationResponse>} Optimization results with weights and metrics
 * @throws {Error} If optimization fails (infeasible constraints, solver error)
 * 
 * @example
 * const result = await optimizePortfolio({
 *   method: 'Mean-CVaR Trade-off',
 *   min_weight: 0.02,
 *   max_weight: 0.10,
 *   risk_free_rate: 0.02,
 *   cvar_alpha: 0.95,
 *   risk_aversion: 0.7, // 70% weight on return, 30% on risk
 *   exp_risk_aversion: 2.0,
 *   constraint_type: 'volatility'
 * });
 * 
 * console.log(`Expected Return: ${(result.metrics.expected_return * 100).toFixed(2)}%`);
 * console.log(`Sharpe Ratio: ${result.metrics.sharpe_ratio.toFixed(3)}`);
 */
export async function optimizePortfolio(request: OptimizationRequest): Promise<OptimizationResponse> {
  const response = await fetch(`${API_BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error('Optimization failed');
  return response.json();
}

/**
 * Fetches the efficient frontier for visualization.
 * 
 * The efficient frontier shows the optimal risk-return trade-off for
 * portfolios with the specified constraints. Each point represents
 * a portfolio that maximizes return for its level of risk.
 * 
 * @async
 * @function fetchEfficientFrontier
 * @param {number} [minWeight=0] - Minimum weight per asset (0-1)
 * @param {number} [maxWeight=1] - Maximum weight per asset (0-1)
 * @param {number} [nPoints=20] - Number of points to calculate on the frontier
 * @param {number} [riskFreeRate=0] - Risk-free rate for Sharpe ratio calculation
 * @returns {Promise<EfficientFrontierPoint[]>} Array of frontier points
 * @throws {Error} If the frontier calculation fails
 * 
 * @example
 * // Get 50 points on the efficient frontier
 * const frontier = await fetchEfficientFrontier(0.01, 0.15, 50, 0.02);
 * 
 * // Find the maximum Sharpe ratio portfolio
 * const maxSharpe = frontier.reduce((best, p) => 
 *   p.sharpe_ratio > best.sharpe_ratio ? p : best
 * );
 */
export async function fetchEfficientFrontier(
  minWeight: number = 0,
  maxWeight: number = 1,
  nPoints: number = 20,
  riskFreeRate: number = 0
): Promise<EfficientFrontierPoint[]> {
  const params = new URLSearchParams({
    min_weight: minWeight.toString(),
    max_weight: maxWeight.toString(),
    n_points: nPoints.toString(),
    risk_free_rate: riskFreeRate.toString(),
  });
  const response = await fetch(`${API_BASE}/efficient-frontier?${params}`);
  if (!response.ok) throw new Error('Failed to fetch efficient frontier');
  return response.json();
}

/**
 * Checks the health status of the backend API.
 * 
 * Use this to verify the API is running and has data loaded before
 * making other requests. Returns `true` only if both conditions are met.
 * 
 * @async
 * @function checkHealth
 * @returns {Promise<boolean>} True if API is healthy and data is loaded
 * 
 * @example
 * // Check connection before showing the UI
 * const isConnected = await checkHealth();
 * if (!isConnected) {
 *   showError('Unable to connect to the optimization server');
 * }
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    const data = await response.json();
    return data.status === 'healthy' && data.data_loaded;
  } catch {
    return false;
  }
}

/**
 * Response from file upload endpoint.
 * 
 * @interface UploadResponse
 * @property {string} status - Upload status ('success')
 * @property {number} n_assets - Number of assets in the uploaded file
 * @property {number} n_scenarios - Number of scenarios (rows) in the data
 * @property {string[]} asset_names - List of asset identifiers
 */
export interface UploadResponse {
  status: string;
  n_assets: number;
  n_scenarios: number;
  asset_names: string[];
}

/**
 * Uploads custom returns data from a CSV or Excel file.
 * 
 * The file should have scenarios as rows and assets as columns.
 * The first column is treated as scenario identifiers (ignored in calculations).
 * 
 * **Supported formats:**
 * - CSV (.csv)
 * - Excel (.xlsx, .xls)
 * 
 * @async
 * @function uploadData
 * @param {File} file - The file to upload
 * @returns {Promise<UploadResponse>} Upload result with asset information
 * @throws {Error} If file format is invalid or upload fails
 * 
 * @example
 * // Handle file input change
 * const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
 *   const file = e.target.files?.[0];
 *   if (file) {
 *     try {
 *       const result = await uploadData(file);
 *       console.log(`Uploaded ${result.n_assets} assets with ${result.n_scenarios} scenarios`);
 *     } catch (error) {
 *       console.error('Upload failed:', error.message);
 *     }
 *   }
 * };
 */
export async function uploadData(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }
  
  return response.json();
}

/**
 * Resets the data to the default sample dataset.
 * 
 * Use this to restore the original demo data after uploading custom data.
 * This will clear any uploaded data and reinitialize the optimizer.
 * 
 * @async
 * @function resetData
 * @returns {Promise<void>}
 * @throws {Error} If the reset operation fails
 * 
 * @example
 * // Reset button handler
 * const handleReset = async () => {
 *   await resetData();
 *   await refetchAssets();
 *   showToast('Data reset to default');
 * };
 */
export async function resetData(): Promise<void> {
  const response = await fetch(`${API_BASE}/reset`, {
    method: 'POST',
  });
  
  if (!response.ok) {
    throw new Error('Failed to reset data');
  }
}
