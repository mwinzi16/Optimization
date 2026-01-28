"""
Portfolio Optimizer - FastAPI Backend
======================================

A comprehensive REST API for portfolio optimization with support for
scenario-based analysis and multiple optimization strategies.

This module provides:
    - Multiple optimization strategies (Sharpe, Variance, CVaR, Utility-based)
    - Scenario-based risk analysis
    - Efficient frontier computation
    - File upload for custom return data

Key Classes:
    - CatBondOptimizer: Core optimization engine
    - OptimizationRequest: Pydantic model for optimization parameters
    - OptimizationResponse: Structured response with weights and metrics

API Endpoints:
    - GET  /api/health           - Health check
    - GET  /api/assets           - List available assets
    - POST /api/optimize         - Run optimization
    - GET  /api/efficient-frontier - Compute efficient frontier
    - POST /api/upload           - Upload custom data
    - POST /api/reset            - Reset to sample data

Example Usage:
    >>> import requests
    >>> response = requests.post(
    ...     "http://localhost:8000/api/optimize",
    ...     json={
    ...         "method": "Maximum Sharpe Ratio",
    ...         "min_weight": 0.01,
    ...         "max_weight": 0.15,
    ...         "risk_free_rate": 0.02
    ...     }
    ... )
    >>> data = response.json()
    >>> print(f"Sharpe Ratio: {data['metrics']['sharpe_ratio']:.3f}")

Authors:
    Portfolio Optimizer Team

Version:
    2.0.0

License:
    MIT
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
import os
import io
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from pathlib import Path
import cvxpy as cp
from scipy.optimize import minimize
from dataclasses import dataclass

app = FastAPI(
    title="Portfolio Optimizer API",
    description="Advanced portfolio optimization with multiple strategies",
    version="2.0.0"
)

# Load runtime config (CORS, API key, upload limits, bind host)
from .config import CORS_ORIGINS, API_KEY, ALLOW_ANONYMOUS, MAX_UPLOAD_SIZE, BIND_HOST, BIND_PORT, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW, REDACT_KEYS
from .utils.validation import validate_file_extension
from .utils.logger import safe_log_dict, logger
from .ratelimit import RateLimitMiddleware


# CORS middleware for frontend (read from env via backend.config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate-limit middleware (in-memory). For multi-worker deployments use Redis-backed limiter.
app.add_middleware(RateLimitMiddleware, max_requests=RATE_LIMIT_REQUESTS, window_seconds=RATE_LIMIT_WINDOW)

# Simple API key header scheme. For production use a full OAuth2/JWT flow.
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_scheme)) -> bool:
    """Dependency to protect sensitive endpoints with a single API key.

    Behavior:
      - If `ALLOW_ANONYMOUS` is true, skip checks (development convenience).
      - If `API_KEY` is not configured and anonymous is false, return 500.
      - Otherwise require header `X-API-Key` to match.
    """
    if ALLOW_ANONYMOUS:
        return True
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured on server")
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

# ============================================================================
# DATA MODELS
# ============================================================================

class OptimizationRequest(BaseModel):
    """
    Request model for portfolio optimization.
    
    This model validates and documents all parameters needed for optimization.
    Different optimization methods use different subsets of these parameters.
    
    Attributes:
        method: Optimization method to use. One of:
            - "Maximum Sharpe Ratio"
            - "Minimum Variance"  
            - "Minimum CVaR"
            - "Mean-CVaR Trade-off"
            - "Maximum Return (Constrained)"
            - "Exponential Utility (CARA)"
        min_weight: Minimum allocation per asset (0.0-1.0)
        max_weight: Maximum allocation per asset (0.0-1.0)
        risk_free_rate: Annual risk-free rate for Sharpe calculation (0.02 = 2%)
        cvar_alpha: Tail probability for CVaR (0.05 = 95% confidence)
        risk_aversion: Trade-off for Mean-CVaR (higher = more risk averse)
        exp_risk_aversion: CARA coefficient (0=seeking, 0.5=neutral, 1=averse)
        max_volatility: Maximum portfolio volatility constraint
        max_cvar: Maximum portfolio CVaR constraint
        constraint_type: Type of constraint for max return ("volatility" or "cvar")
        cvar_constraint_alpha: Alpha for CVaR constraint
    
    Example:
        >>> request = OptimizationRequest(
        ...     method="Maximum Sharpe Ratio",
        ...     min_weight=0.01,
        ...     max_weight=0.15,
        ...     risk_free_rate=0.02
        ... )
    """
    method: str = Field(..., description="Optimization method")
    min_weight: float = Field(0.0, ge=0.0, le=1.0)
    max_weight: float = Field(1.0, ge=0.0, le=1.0)
    risk_free_rate: float = Field(0.0, ge=0.0, le=0.2)
    # Method-specific parameters
    cvar_alpha: float = Field(0.05, ge=0.01, le=0.2)
    risk_aversion: float = Field(1.0, ge=0.01, le=5.0)
    exp_risk_aversion: float = Field(0.5, ge=0.01, le=1.0)
    max_volatility: Optional[float] = Field(None, ge=0.01, le=0.5)
    max_cvar: Optional[float] = Field(None, ge=0.01, le=0.8)
    constraint_type: str = Field("volatility", description="volatility or cvar")
    cvar_constraint_alpha: float = Field(0.05, ge=0.01, le=0.2)


class OptimizationResponse(BaseModel):
    """
    Response model containing optimization results.
    
    Includes optimal portfolio weights, risk/return metrics, scenario-level
    returns, and comprehensive distribution statistics.
    
    Attributes:
        status: Optimization status ("optimal" or "fallback: <reason>")
        method: Method used for optimization
        weights: Dictionary mapping asset names to portfolio weights (sum to 1)
        metrics: Risk and return metrics including:
            - expected_return: Annualized expected return
            - volatility: Annualized standard deviation
            - sharpe_ratio: Risk-adjusted return
            - var_*: Value at Risk at various confidence levels
            - cvar_*: Conditional VaR at various confidence levels
            - max_drawdown: Maximum loss in any scenario
        portfolio_returns: Array of returns for each scenario
        distribution_stats: Detailed statistics including percentiles,
            skewness, kurtosis, and probability metrics
    """
    status: str
    method: str
    weights: Dict[str, float]
    metrics: Dict[str, float]
    portfolio_returns: List[float]
    distribution_stats: Dict[str, float]
    best_scenario_returns: Dict[str, float]  # Asset returns in the best portfolio scenario
    var90_scenario_returns: Dict[str, float]  # Asset returns in the VaR90 scenario
    var95_scenario_returns: Dict[str, float]  # Asset returns in the VaR95 scenario
    var99_scenario_returns: Dict[str, float]  # Asset returns in the VaR99 scenario
    asset_mean_returns: Dict[str, float]  # Mean return for each asset (for expected loss)


class AssetInfo(BaseModel):
    """
    Information about a single asset in the portfolio universe.
    
    Provides summary statistics computed from the scenario returns data,
    including expected return, volatility, and tail risk measures.
    
    Attributes:
        name: Unique identifier for the asset
        expected_return: Mean return across all scenarios
        no_loss_return: Maximum possible return (no catastrophe)
        expected_loss: Difference between no-loss and expected return
        volatility: Standard deviation of returns
        var_90: 90th percentile Value at Risk (10% tail)
        var_95: 95th percentile Value at Risk (5% tail)
        var_99: 99th percentile Value at Risk (1% tail)
        cvar_95: Expected Shortfall (CVaR) at 95% confidence
    """
    name: str
    expected_return: float
    no_loss_return: float
    expected_loss: float
    volatility: float
    var_90: float
    var_95: float
    var_99: float
    cvar_95: float


class EfficientFrontierPoint(BaseModel):
    """
    A single point on the efficient frontier.
    
    The efficient frontier represents the set of Pareto-optimal portfolios
    that offer the highest expected return for each level of risk.
    
    Attributes:
        expected_return: Expected portfolio return at this point
        volatility: Portfolio standard deviation (risk measure)
        sharpe_ratio: Risk-adjusted return (return / volatility)
        cvar_95: Conditional Value at Risk at 95% confidence
    """
    expected_return: float
    volatility: float
    sharpe_ratio: float
    cvar_95: float


# ============================================================================
# OPTIMIZER CLASS
# ============================================================================

class CatBondOptimizer:
    """
    Portfolio optimizer for catastrophe bond and ILS portfolios.
    
    This class implements multiple optimization strategies using scenario-based
    returns data. It supports convex optimization via CVXPY for tractable
    problems and SciPy for non-convex utility maximization.
    
    Optimization Methods:
        - max_sharpe: Maximize risk-adjusted return (Sharpe ratio)
        - min_variance: Minimize portfolio volatility
        - min_cvar: Minimize tail risk (Conditional Value at Risk)
        - mean_cvar: Trade-off between return and CVaR
        - max_return: Maximize return with risk constraints
        - exponential_utility: CARA utility function optimization
    
    Attributes:
        rf (float): Risk-free rate used for Sharpe calculations
        returns (pd.DataFrame): Adjusted scenario returns
        assets (List[str]): Asset names/identifiers
        n_assets (int): Number of assets in universe
        n_scenarios (int): Number of return scenarios
        mean_returns (np.ndarray): Mean return per asset
        cov_matrix (np.ndarray): Covariance matrix of returns
        returns_matrix (np.ndarray): Raw returns as numpy array
    
    Example:
        >>> import pandas as pd
        >>> returns_df = pd.DataFrame({
        ...     'Bond_A': [0.05, -0.02, 0.08, -0.15, 0.06],
        ...     'Bond_B': [0.04, 0.03, 0.05, -0.10, 0.04]
        ... })
        >>> optimizer = CatBondOptimizer(returns_df, risk_free_rate=0.02)
        >>> result = optimizer.optimize_max_sharpe(min_weight=0.1, max_weight=0.9)
        >>> print(f"Weights: {result['weights']}")
    
    Note:
        The risk-free rate is subtracted from returns during initialization,
        so all internal calculations use excess returns.
    """
    
    def __init__(self, returns_df: pd.DataFrame, risk_free_rate: float = 0.0):
        """
        Initialize the optimizer.
        
        Args:
            returns_df: DataFrame with scenario returns per asset
            risk_free_rate: Risk-free rate (as decimal, e.g., 0.05 for 5%). 
                           This is SUBTRACTED from the returns since it's assumed
                           to be already embedded in the input distribution.
        """
        self.rf = risk_free_rate
        
        # Store original returns for best scenario calculations
        self.original_returns_matrix = returns_df.values
        
        # Subtract risk-free rate from returns (it's embedded in the distribution)
        adjusted_returns = returns_df - risk_free_rate
        
        self.returns = adjusted_returns
        self.assets = list(returns_df.columns)
        self.n_assets = len(self.assets)
        self.n_scenarios = len(returns_df)
        
        self.mean_returns = adjusted_returns.mean().values
        self.cov_matrix = adjusted_returns.cov().values
        self.returns_matrix = adjusted_returns.values
        
        # Store asset max returns (coupons) for no-loss return calculation
        # No-loss return = weighted sum of individual asset max returns (full coupon scenario)
        self.asset_max_returns = adjusted_returns.max().values
    
    def _compute_portfolio_metrics(self, weights: np.ndarray) -> dict:
        """
        Compute comprehensive risk and return metrics for a portfolio.
        
        Args:
            weights: Portfolio weights as numpy array (should sum to 1)
            
        Returns:
            Dictionary containing:
                - expected_return: Mean portfolio return
                - volatility: Portfolio standard deviation
                - sharpe_ratio: Return / volatility ratio
                - var_*: Value at Risk at 90/95/98/99% confidence
                - cvar_*: Conditional VaR at 90/95/98/99% confidence
                - max_drawdown: Worst scenario return
        """
        # Use ORIGINAL returns for all metrics to be consistent with distribution_stats
        port_returns = self.original_returns_matrix @ weights
        
        exp_return = float(np.mean(port_returns))
        volatility = float(np.std(port_returns))
        # Sharpe ratio: (return - rf) / volatility
        sharpe = float((exp_return - self.rf) / volatility) if volatility > 0 else 0.0
        
        var_90 = float(np.percentile(port_returns, 10))
        var_95 = float(np.percentile(port_returns, 5))
        var_98 = float(np.percentile(port_returns, 2))
        var_99 = float(np.percentile(port_returns, 1))
        cvar_90 = float(port_returns[port_returns <= var_90].mean()) if (port_returns <= var_90).any() else var_90
        cvar_95 = float(port_returns[port_returns <= var_95].mean()) if (port_returns <= var_95).any() else var_95
        cvar_98 = float(port_returns[port_returns <= var_98].mean()) if (port_returns <= var_98).any() else var_98
        cvar_99 = float(port_returns[port_returns <= var_99].mean()) if (port_returns <= var_99).any() else var_99
        
        max_drawdown = float(port_returns.min())
        
        return {
            "expected_return": exp_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe,
            "var_90": var_90,
            "var_95": var_95,
            "var_98": var_98,
            "var_99": var_99,
            "cvar_90": cvar_90,
            "cvar_95": cvar_95,
            "cvar_98": cvar_98,
            "cvar_99": cvar_99,
            "max_drawdown": max_drawdown,
        }
    
    def _compute_distribution_stats(self, weights: np.ndarray) -> dict:
        """
        Compute detailed distribution statistics for portfolio returns.
        
        Provides comprehensive analysis of the return distribution including
        moments, percentiles, and probability metrics for risk assessment.
        
        Args:
            weights: Portfolio weights as numpy array
            
        Returns:
            Dictionary containing:
                - mean, median, std: Central tendency and dispersion
                - skewness, kurtosis: Distribution shape
                - min, max: Return range
                - expected_loss, no_loss_return: ILS-specific metrics
                - prob_*: Probability of various loss thresholds
                - p1 through p99: Percentile values
        """
        # Use ORIGINAL (unadjusted) returns for all distribution statistics
        # This ensures no_loss_return = max of distribution
        port_returns = self.original_returns_matrix @ weights
        
        # No-loss return = maximum portfolio return (best year)
        no_loss_return = float(np.max(port_returns))
        
        # Expected loss = mean - no_loss
        mean_return = float(np.mean(port_returns))
        expected_loss = mean_return - no_loss_return
        
        return {
            "mean": mean_return,
            "median": float(np.median(port_returns)),
            "std": float(np.std(port_returns)),
            "skewness": float(pd.Series(port_returns).skew()),
            "kurtosis": float(pd.Series(port_returns).kurtosis()),
            "min": float(np.min(port_returns)),
            "max": float(np.max(port_returns)),
            "expected_loss": expected_loss,
            "no_loss_return": no_loss_return,
            "prob_positive": float((port_returns > 0).mean()),
            "prob_loss_5": float((port_returns < -0.05).mean()),
            "prob_loss_10": float((port_returns < -0.10).mean()),
            "prob_loss_25": float((port_returns < -0.25).mean()),
            "prob_loss_50": float((port_returns < -0.50).mean()),
            "p1": float(np.percentile(port_returns, 1)),
            "p5": float(np.percentile(port_returns, 5)),
            "p10": float(np.percentile(port_returns, 10)),
            "p25": float(np.percentile(port_returns, 25)),
            "p50": float(np.percentile(port_returns, 50)),
            "p75": float(np.percentile(port_returns, 75)),
            "p90": float(np.percentile(port_returns, 90)),
            "p95": float(np.percentile(port_returns, 95)),
            "p99": float(np.percentile(port_returns, 99)),
        }
    
    def optimize_max_sharpe(self, min_weight: float = 0.0, max_weight: float = 1.0) -> dict:
        """
        Maximize Sharpe Ratio using the transformation method.
        We solve: min y'Σy  s.t. μ'y = 1, y >= 0
        Then normalize: w = y / sum(y)
        
        This is equivalent to maximizing μ'w / sqrt(w'Σw)
        
        Note: self.mean_returns is already excess returns (rf subtracted in __init__)
        """
        # Check if any positive excess returns exist
        if np.all(self.mean_returns <= 0):
            # All returns negative after rf subtraction - fall back to min variance
            return self.optimize_min_variance(min_weight, max_weight)
        
        y = cp.Variable(self.n_assets)
        # mean_returns is already excess return (rf was subtracted from all returns)
        portfolio_var = cp.quad_form(y, self.cov_matrix)
        
        # Key constraint: expected excess return = 1 (this is the transformation trick)
        constraints = [
            self.mean_returns @ y == 1,  # Fixed excess return (transformation)
            y >= 0  # Non-negative (will be normalized to weights)
        ]
        
        problem = cp.Problem(cp.Minimize(portfolio_var), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal" or y.value is None or np.sum(y.value) <= 0:
            # Fallback: try with relaxed constraints or equal weight
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"fallback: {problem.status}"
        else:
            # Normalize y to get actual portfolio weights
            y_vals = np.maximum(y.value, 0)  # Ensure non-negative
            weights = y_vals / np.sum(y_vals)
            
            # Apply min/max weight constraints via post-processing if needed
            if min_weight > 0 or max_weight < 1:
                weights = np.clip(weights, min_weight, max_weight)
                weights = weights / np.sum(weights)  # Re-normalize
            
            status = "optimal"
        
        return {"weights": weights, "status": status, "method": "max_sharpe"}
    
    def optimize_min_variance(self, min_weight: float = 0.0, max_weight: float = 1.0,
                               target_return: float = None) -> dict:
        """
        Minimize portfolio variance (volatility squared).
        
        Finds the minimum variance portfolio using convex optimization.
        Optionally constrains to achieve a minimum target return.
        
        Args:
            min_weight: Minimum allocation per asset (default: 0.0)
            max_weight: Maximum allocation per asset (default: 1.0)
            target_return: Optional minimum expected return constraint
            
        Returns:
            Dictionary with 'weights', 'status', and 'method' keys
            
        Note:
            Uses CVXPY with CLARABEL solver for guaranteed global optimum.
        """
        w = cp.Variable(self.n_assets)
        portfolio_var = cp.quad_form(w, self.cov_matrix)
        
        constraints = [cp.sum(w) == 1, w >= min_weight, w <= max_weight]
        if target_return is not None:
            constraints.append(self.mean_returns @ w >= target_return)
        
        problem = cp.Problem(cp.Minimize(portfolio_var), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"fallback: {problem.status}"
        else:
            weights = w.value
            status = "optimal"
        
        return {"weights": weights, "status": status, "method": "min_variance"}
    
    def optimize_min_cvar(self, alpha: float = 0.05, min_weight: float = 0.0,
                          max_weight: float = 1.0) -> dict:
        """
        Minimize Conditional Value at Risk (Expected Shortfall).
        
        CVaR represents the expected loss in the worst (1-alpha)% of scenarios.
        Uses the Rockafellar-Uryasev formulation for convex optimization.
        
        Args:
            alpha: Tail probability (0.05 = 95% confidence, default)
            min_weight: Minimum allocation per asset
            max_weight: Maximum allocation per asset
            
        Returns:
            Dictionary with 'weights', 'status', and 'method' keys
            
        Example:
            >>> result = optimizer.optimize_min_cvar(alpha=0.05)
            # Minimizes expected loss in worst 5% of scenarios
        """
        w = cp.Variable(self.n_assets)
        z = cp.Variable()
        u = cp.Variable(self.n_scenarios)
        
        port_returns = self.returns_matrix @ w
        objective = z + (1 / (alpha * self.n_scenarios)) * cp.sum(u)
        
        constraints = [cp.sum(w) == 1, w >= min_weight, w <= max_weight,
                      u >= 0, u >= -port_returns - z]
        
        problem = cp.Problem(cp.Minimize(objective), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"fallback: {problem.status}"
        else:
            weights = w.value
            status = "optimal"
        
        return {"weights": weights, "status": status, "method": f"min_cvar_{int((1-alpha)*100)}"}
    
    def optimize_mean_cvar(self, alpha: float = 0.05, risk_aversion: float = 1.0,
                           min_weight: float = 0.0, max_weight: float = 1.0) -> dict:
        """
        Optimize the mean-CVaR trade-off.
        
        Balances expected return against tail risk using a weighted objective:
            minimize: -E[return] + risk_aversion * CVaR
        
        Args:
            alpha: Tail probability for CVaR (default: 0.05)
            risk_aversion: Weight on CVaR penalty (higher = more risk averse)
            min_weight: Minimum allocation per asset
            max_weight: Maximum allocation per asset
            
        Returns:
            Dictionary with 'weights', 'status', and 'method' keys
            
        Note:
            risk_aversion=0 maximizes return only
            risk_aversion→∞ minimizes CVaR only
        """
        w = cp.Variable(self.n_assets)
        z = cp.Variable()
        u = cp.Variable(self.n_scenarios)
        
        port_returns = self.returns_matrix @ w
        exp_return = self.mean_returns @ w
        cvar = z + (1 / (alpha * self.n_scenarios)) * cp.sum(u)
        
        objective = -exp_return + risk_aversion * cvar
        
        constraints = [cp.sum(w) == 1, w >= min_weight, w <= max_weight,
                      u >= 0, u >= -port_returns - z]
        
        problem = cp.Problem(cp.Minimize(objective), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"fallback: {problem.status}"
        else:
            weights = w.value
            status = "optimal"
        
        return {"weights": weights, "status": status, "method": f"mean_cvar_lambda_{risk_aversion}"}
    
    def optimize_max_return(self, max_volatility: float = None, max_cvar: float = None,
                            alpha: float = 0.05, min_weight: float = 0.0,
                            max_weight: float = 1.0) -> dict:
        """
        Maximize expected return subject to risk constraints.
        
        Finds the highest-return portfolio that satisfies either a volatility
        or CVaR constraint (or both).
        
        Args:
            max_volatility: Maximum allowed portfolio volatility
            max_cvar: Maximum allowed portfolio CVaR
            alpha: Tail probability for CVaR constraint
            min_weight: Minimum allocation per asset
            max_weight: Maximum allocation per asset
            
        Returns:
            Dictionary with 'weights', 'status', and 'method' keys
            
        Example:
            >>> # Max return with 10% volatility limit
            >>> result = optimizer.optimize_max_return(max_volatility=0.10)
            
            >>> # Max return with 15% CVaR limit
            >>> result = optimizer.optimize_max_return(max_cvar=0.15, alpha=0.05)
        """
        w = cp.Variable(self.n_assets)
        
        constraints = [cp.sum(w) == 1, w >= min_weight, w <= max_weight]
        
        if max_volatility is not None:
            portfolio_var = cp.quad_form(w, self.cov_matrix)
            constraints.append(portfolio_var <= max_volatility ** 2)
        
        if max_cvar is not None:
            z = cp.Variable()
            u = cp.Variable(self.n_scenarios)
            port_returns = self.returns_matrix @ w
            cvar = z + (1 / (alpha * self.n_scenarios)) * cp.sum(u)
            constraints.extend([u >= 0, u >= -port_returns - z, cvar <= max_cvar])
        
        objective = -self.mean_returns @ w
        
        problem = cp.Problem(cp.Minimize(objective), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"fallback: {problem.status}"
        else:
            weights = w.value
            status = "optimal"
        
        return {"weights": weights, "status": status, "method": "max_return"}
    
    def optimize_exponential_utility(self, risk_aversion: float = 0.5,
                                      min_weight: float = 0.0,
                                      max_weight: float = 1.0) -> dict:
        """
        Exponential (CARA) utility optimization.
        
        Utility function: U(W) = -e^(-C*W)
        Value function: V = -(e^(-C*50*r)) / C
        
        Risk aversion parameter mapping:
        - 0 = Risk-seeking (C < 0): prefers higher variance for upside
        - 0.5 = Risk-neutral (C = 0): maximizes expected return
        - 1 = Risk-averse (C > 0): penalizes variance/downside
        
        C_actual = (risk_aversion - 0.5) * 2, so:
        - risk_aversion=0 → C=-1 (risk-seeking)
        - risk_aversion=0.5 → C=0 (risk-neutral)
        - risk_aversion=1 → C=+1 (risk-averse)
        """
        scale = 50
        # Transform: 0 = seeking (-1), 0.5 = neutral (0), 1 = averse (+1)
        C = (risk_aversion - 0.5) * 2
        
        # Risk-neutral case: just maximize expected return
        if abs(C) < 1e-6:
            def negative_expected_return(weights):
                return -np.mean(self.returns_matrix @ weights)
            
            def gradient(weights):
                return -np.mean(self.returns_matrix, axis=0)
            
            constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
            bounds = [(min_weight, max_weight) for _ in range(self.n_assets)]
            w0 = np.ones(self.n_assets) / self.n_assets
            
            result = minimize(
                negative_expected_return, w0,
                method="SLSQP", jac=gradient,
                bounds=bounds, constraints=constraints,
                options={"ftol": 1e-10, "maxiter": 1000}
            )
        else:
            def negative_expected_value(weights):
                # Portfolio returns
                port_returns = self.returns_matrix @ weights
                # V = -(e^(-C*50*r)) / C for each scenario
                # Maximize E[V] = -(1/C) * E[e^(-C*50*r)]
                # For C > 0 (risk-averse): minimize E[e^(-C*50*r)]
                # For C < 0 (risk-seeking): maximize E[e^(-C*50*r)] = minimize -E[e^(-C*50*r)]
                exp_terms = np.exp(-C * scale * port_returns)
                if C > 0:
                    return np.mean(exp_terms)  # Minimize this
                else:
                    return -np.mean(exp_terms)  # Minimize negative = maximize
            
            def gradient(weights):
                port_returns = self.returns_matrix @ weights
                exp_terms = np.exp(-C * scale * port_returns)
                grad = np.zeros(self.n_assets)
                for i in range(self.n_assets):
                    if C > 0:
                        grad[i] = np.mean(-C * scale * self.returns_matrix[:, i] * exp_terms)
                    else:
                        grad[i] = -np.mean(-C * scale * self.returns_matrix[:, i] * exp_terms)
                return grad
            
            constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
            bounds = [(min_weight, max_weight) for _ in range(self.n_assets)]
            w0 = np.ones(self.n_assets) / self.n_assets
            
            result = minimize(
                negative_expected_value, w0,
                method="SLSQP", jac=gradient,
                bounds=bounds, constraints=constraints,
                options={"ftol": 1e-10, "maxiter": 1000}
            )
        
        if result.success:
            weights = result.x / result.x.sum()
            status = "optimal"
        else:
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"fallback: {result.message}"
        
        return {"weights": weights, "status": status, "method": f"exponential_utility_C_{C:.2f}"}
    
    def efficient_frontier(self, n_points: int = 20, min_weight: float = 0.0,
                           max_weight: float = 1.0) -> List[dict]:
        min_var_result = self.optimize_min_variance(min_weight, max_weight)
        min_var_metrics = self._compute_portfolio_metrics(min_var_result["weights"])
        
        max_return = float(self.mean_returns.max())
        min_return = min_var_metrics["expected_return"]
        
        target_returns = np.linspace(min_return, max_return * 0.95, n_points)
        
        frontier_data = []
        for target in target_returns:
            result = self.optimize_min_variance(min_weight, max_weight, target_return=target)
            if "optimal" in result["status"]:
                metrics = self._compute_portfolio_metrics(result["weights"])
                frontier_data.append({
                    "expected_return": metrics["expected_return"],
                    "volatility": metrics["volatility"],
                    "sharpe_ratio": metrics["sharpe_ratio"],
                    "cvar_95": metrics["cvar_95"],
                })
        
        return frontier_data


# ============================================================================
# GLOBAL STATE
# ============================================================================

# Load data on startup
DATA_PATH = Path(__file__).parent.parent / "data" / "scenario_returns.csv"
returns_df = None
optimizer = None

def load_data():
    global returns_df, optimizer
    if DATA_PATH.exists():
        returns_df = pd.read_csv(DATA_PATH, index_col=0)
        optimizer = CatBondOptimizer(returns_df, risk_free_rate=0.0)
    else:
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")

@app.on_event("startup")
async def startup_event():
    load_data()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "data_loaded": returns_df is not None}


@app.post("/api/upload")
async def upload_data(file: UploadFile = File(...), _auth: bool = Depends(verify_api_key)):
    """
    Upload a CSV file with scenario returns.
    Expected format: First column = scenario index, other columns = asset returns.
    """
    global returns_df, optimizer
    
    try:
        contents = await file.read()
        # Avoid logging file contents; only log metadata safely
        safe_log_dict(logger, {"filename": file.filename, "size": len(contents)}, redact_keys=REDACT_KEYS)

        # Enforce upload size limits
        if len(contents) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large. Max size = {MAX_UPLOAD_SIZE} bytes")

        # Validate extension using shared helper
        ok, info = validate_file_extension(file.filename)
        if not ok:
            raise HTTPException(status_code=400, detail=info)

        # Try to read as CSV/Excel
        if file.filename.lower().endswith('.csv'):
            # Respect content type when possible
            df = pd.read_csv(io.BytesIO(contents), index_col=0)
        elif file.filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents), index_col=0)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel.")
        
        # Validate data
        if df.empty:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Convert to numeric where possible, but first check for potential CSV/Excel
        # formula injection: any string cell starting with =, +, -, @ should be rejected
        object_cols = df.select_dtypes(include=['object']).columns.tolist()
        if object_cols:
            for col in object_cols:
                # Vectorized check for leading dangerous characters
                series = df[col].astype(str).fillna("")
                if series.str.match(r'^[=+\-@]').any():
                    raise HTTPException(status_code=400, detail="File contains potentially dangerous formula cells. Remove leading =, +, - or @ from values.")

        # Convert to numeric, coerce errors
        df = df.apply(pd.to_numeric, errors='coerce')
        
        # Drop rows/cols with all NaN
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        
        if df.shape[1] < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 assets")
        
        if df.shape[0] < 100:
            raise HTTPException(status_code=400, detail="Need at least 100 scenarios")
        
        # Replace in-memory dataset only after validation succeeds
        returns_df = df
        optimizer = CatBondOptimizer(returns_df, risk_free_rate=0.0)
        
        return {
            "status": "success",
            "n_assets": df.shape[1],
            "n_scenarios": df.shape[0],
            "asset_names": list(df.columns)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


@app.post("/api/reset")
async def reset_data(_auth: bool = Depends(verify_api_key)):
    """Reset to default sample data."""
    global returns_df, optimizer
    try:
        load_data()
        logger.info("Data reset to sample data via API reset endpoint")
        return {"status": "success", "message": "Reset to sample data"}
    except Exception as e:
        logger.exception("Failed to reset data")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/assets", response_model=List[AssetInfo])
async def get_assets():
    if returns_df is None:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    assets = []
    for col in returns_df.columns:
        asset_returns = returns_df[col].values
        
        # No-loss return = max of the distribution
        no_loss_return = float(np.max(asset_returns))
        
        # Expected loss = mean - max
        mean_return = float(np.mean(asset_returns))
        expected_loss = mean_return - no_loss_return
        
        # VaR at different confidence levels
        var_90 = float(np.percentile(asset_returns, 10))
        var_95 = float(np.percentile(asset_returns, 5))
        var_99 = float(np.percentile(asset_returns, 1))
        cvar_95 = float(asset_returns[asset_returns <= var_95].mean())
        
        assets.append(AssetInfo(
            name=col,
            expected_return=mean_return,
            no_loss_return=no_loss_return,
            expected_loss=expected_loss,
            volatility=float(np.std(asset_returns)),
            var_90=var_90,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95
        ))
    
    return assets


@app.post("/api/optimize", response_model=OptimizationResponse)
async def optimize_portfolio(request: OptimizationRequest, _auth: bool = Depends(verify_api_key)):
    global optimizer
    
    if returns_df is None:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    # Update optimizer with new risk-free rate
    optimizer = CatBondOptimizer(returns_df, risk_free_rate=request.risk_free_rate)
    
    # Run optimization based on method
    method = request.method.lower().replace(" ", "_").replace("(", "").replace(")", "")
    
    if method == "maximum_sharpe_ratio" or method == "max_sharpe":
        result = optimizer.optimize_max_sharpe(request.min_weight, request.max_weight)
    elif method == "minimum_variance" or method == "min_variance":
        result = optimizer.optimize_min_variance(request.min_weight, request.max_weight)
    elif method == "minimum_cvar" or method == "min_cvar":
        result = optimizer.optimize_min_cvar(request.cvar_alpha, request.min_weight, request.max_weight)
    elif method == "mean-cvar_trade-off" or method == "mean_cvar":
        result = optimizer.optimize_mean_cvar(request.cvar_alpha, request.risk_aversion,
                                               request.min_weight, request.max_weight)
    elif method == "maximum_return_constrained" or method == "max_return":
        if request.constraint_type == "volatility":
            result = optimizer.optimize_max_return(
                max_volatility=request.max_volatility or 0.15,
                min_weight=request.min_weight, max_weight=request.max_weight
            )
        else:
            result = optimizer.optimize_max_return(
                max_cvar=request.max_cvar or 0.25,
                alpha=request.cvar_constraint_alpha,
                min_weight=request.min_weight, max_weight=request.max_weight
            )
    elif method == "exponential_utility_cara" or method == "exponential_utility":
        result = optimizer.optimize_exponential_utility(
            request.exp_risk_aversion, request.min_weight, request.max_weight
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown optimization method: {request.method}")
    
    weights = result["weights"]
    metrics = optimizer._compute_portfolio_metrics(weights)
    dist_stats = optimizer._compute_distribution_stats(weights)
    # Use ORIGINAL (unadjusted) returns for consistency with distribution_stats
    original_portfolio_returns = optimizer.original_returns_matrix @ weights
    portfolio_returns = original_portfolio_returns.tolist()
    
    # Find the best scenario (highest portfolio return) and get each asset's return in that scenario
    best_scenario_idx = int(np.argmax(original_portfolio_returns))
    best_scenario_asset_returns = optimizer.original_returns_matrix[best_scenario_idx, :]
    best_scenario_returns = {asset: float(r) for asset, r in zip(returns_df.columns, best_scenario_asset_returns)}
    
    # Find VaR scenarios (sorted indices, find the scenario at each percentile)
    sorted_indices = np.argsort(original_portfolio_returns)
    n_scenarios = len(original_portfolio_returns)
    var90_idx = sorted_indices[int(n_scenarios * 0.10)]  # 10th percentile
    var95_idx = sorted_indices[int(n_scenarios * 0.05)]  # 5th percentile
    var99_idx = sorted_indices[int(n_scenarios * 0.01)]  # 1st percentile
    
    var90_scenario_returns = {asset: float(r) for asset, r in zip(returns_df.columns, optimizer.original_returns_matrix[var90_idx, :])}
    var95_scenario_returns = {asset: float(r) for asset, r in zip(returns_df.columns, optimizer.original_returns_matrix[var95_idx, :])}
    var99_scenario_returns = {asset: float(r) for asset, r in zip(returns_df.columns, optimizer.original_returns_matrix[var99_idx, :])}
    
    # Mean returns for each asset (for expected loss calculation)
    asset_mean_returns = {asset: float(r) for asset, r in zip(returns_df.columns, optimizer.original_returns_matrix.mean(axis=0))}
    
    return OptimizationResponse(
        status=result["status"],
        method=result["method"],
        weights={asset: float(w) for asset, w in zip(returns_df.columns, weights)},
        metrics=metrics,
        portfolio_returns=portfolio_returns,
        distribution_stats=dist_stats,
        best_scenario_returns=best_scenario_returns,
        var90_scenario_returns=var90_scenario_returns,
        var95_scenario_returns=var95_scenario_returns,
        var99_scenario_returns=var99_scenario_returns,
        asset_mean_returns=asset_mean_returns
    )


@app.get("/api/efficient-frontier", response_model=List[EfficientFrontierPoint])
async def get_efficient_frontier(
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    n_points: int = 20,
    risk_free_rate: float = 0.0
):
    if returns_df is None:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    # Create optimizer with requested risk-free rate
    frontier_optimizer = CatBondOptimizer(returns_df, risk_free_rate=risk_free_rate)
    frontier = frontier_optimizer.efficient_frontier(n_points, min_weight, max_weight)
    return [EfficientFrontierPoint(**point) for point in frontier]


@app.get("/api/scenarios")
async def get_scenarios(sample_size: int = 1000):
    """Get a sample of scenario returns for visualization."""
    if returns_df is None:
        raise HTTPException(status_code=500, detail="Data not loaded")
    
    # Sample scenarios
    n = len(returns_df)
    indices = np.linspace(0, n - 1, min(sample_size, n), dtype=int)
    
    return {
        "scenarios": indices.tolist(),
        "n_total": n,
        "assets": returns_df.columns.tolist()
    }


if __name__ == "__main__":
    import uvicorn
    # Bind to a safe default host/port unless overridden in environment
    uvicorn.run(app, host=BIND_HOST, port=BIND_PORT)
