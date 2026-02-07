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

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Query, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from starlette.responses import JSONResponse
import hmac
import io
import os
import threading
import uuid
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from pathlib import Path
import cvxpy as cp
from scipy.optimize import minimize
from dataclasses import dataclass

# Lifespan context manager (replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    load_data()
    yield

tags_metadata = [
    {"name": "Health", "description": "Health check and status"},
    {"name": "Data", "description": "Data upload and management"},
    {"name": "Portfolio", "description": "Portfolio optimization and analysis"},
]

app = FastAPI(
    title="Portfolio Optimizer API",
    description="Advanced portfolio optimization with multiple strategies",
    version="2.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)

# Load runtime config (CORS, API key, upload limits, bind host)
from .config import CORS_ORIGINS, API_KEY, ALLOW_ANONYMOUS, MAX_UPLOAD_SIZE, BIND_HOST, BIND_PORT, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW, REDACT_KEYS
from .utils.validation import ValidatedOptimizationRequest, validate_file_extension, sanitize_column_names
from .utils.exceptions import OptimizerError, DataError, ValidationError, OptimizationError, ErrorCode
from .utils.cache import optimization_cache, frontier_cache, cached
from .utils.logger import safe_log_dict, logger
from .ratelimit import RateLimitMiddleware


# CORS middleware for frontend (read from env via backend.config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials="*" not in CORS_ORIGINS,  # Disable credentials with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate-limit middleware (in-memory). For multi-worker deployments use Redis-backed limiter.
app.add_middleware(RateLimitMiddleware, max_requests=RATE_LIMIT_REQUESTS, window_seconds=RATE_LIMIT_WINDOW)


def envelope(data=None, meta=None, errors=None):
    """Wrap response in standard envelope."""
    return {
        "data": data,
        "meta": meta or {},
        "errors": errors or [],
    }


@app.exception_handler(OptimizerError)
async def optimizer_error_handler(request, exc: OptimizerError):
    """Central error handler for all optimizer exceptions."""
    status_map = {
        ErrorCode.DATA_NOT_LOADED: 500,
        ErrorCode.INVALID_FILE_FORMAT: 400,
        ErrorCode.OPTIMIZATION_FAILED: 422,
        ErrorCode.INVALID_METHOD: 400,
        ErrorCode.INVALID_WEIGHT_RANGE: 400,
        ErrorCode.INTERNAL_ERROR: 500,
    }
    status_code = status_map.get(exc.code, exc.status_code)
    return JSONResponse(
        status_code=status_code,
        content=envelope(
            errors=[{
                "code": exc.code.value if hasattr(exc.code, 'value') else str(exc.code),
                "message": str(exc),
                "details": exc.details,
            }]
        ),
    )


@app.middleware("http")
async def add_request_id(request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


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
    if not api_key or not hmac.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

# ============================================================================
# DATA MODELS
# ============================================================================

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
            - worst_scenario: Worst scenario return
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
        
        # Ensure covariance matrix is positive semi-definite
        eigenvalues = np.linalg.eigvalsh(self.cov_matrix)
        if eigenvalues.min() < 1e-10:
            self.cov_matrix += np.eye(self.n_assets) * 1e-8  # Tikhonov regularization
        
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
                - worst_scenario: Worst scenario return
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
        
        worst_scenario = float(port_returns.min())
        
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
            "worst_scenario": worst_scenario,
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
            y >= 0,  # Non-negative (will be normalized to weights)
        ]
        # Enforce weight bounds in the transformed space
        if min_weight > 0:
            constraints.append(y >= min_weight * cp.sum(y))
        if max_weight < 1:
            constraints.append(y <= max_weight * cp.sum(y))
        
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
            port_returns_orig = self.original_returns_matrix @ w  # Use original returns for CVaR
            cvar = z + (1 / (alpha * self.n_scenarios)) * cp.sum(u)
            constraints.extend([u >= 0, u >= -port_returns_orig - z, cvar <= max_cvar])
        
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
                exponents = np.clip(-C * scale * port_returns, -500, 500)  # Prevent overflow
                exp_terms = np.exp(exponents)
                if C > 0:
                    return float(np.mean(exp_terms))  # Minimize this
                else:
                    return float(-np.mean(exp_terms))  # Minimize negative = maximize
            
            def gradient(weights):
                port_returns = self.returns_matrix @ weights
                exponents = np.clip(-C * scale * port_returns, -500, 500)
                exp_terms = np.exp(exponents)
                # Vectorized gradient
                grad = np.mean(-C * scale * self.returns_matrix * exp_terms[:, np.newaxis], axis=0)
                if C > 0:
                    return grad
                else:
                    return -grad
            
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
        # Convert min_return to excess-return space to match max_return
        min_return = min_var_metrics["expected_return"] - self.rf
        
        # Cap at 95% of range, handling negative max_return properly
        upper_target = max_return - 0.05 * abs(max_return - min_return) if max_return != min_return else max_return
        target_returns = np.linspace(min_return, upper_target, n_points)
        
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


class _DataStore:
    """Thread-safe container for shared optimizer state."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._returns_df: Optional[pd.DataFrame] = None
        self._optimizer: Optional[CatBondOptimizer] = None

    @property
    def returns_df(self) -> Optional[pd.DataFrame]:
        with self._lock:
            return self._returns_df

    @property
    def optimizer(self) -> Optional[CatBondOptimizer]:
        with self._lock:
            return self._optimizer

    def update(self, returns_df: pd.DataFrame, risk_free_rate: float = 0.0) -> None:
        with self._lock:
            self._returns_df = returns_df
            self._optimizer = CatBondOptimizer(returns_df, risk_free_rate=risk_free_rate)
        # Invalidate all caches when data changes
        optimization_cache.clear()
        frontier_cache.clear()

    def get_optimizer(self, risk_free_rate: float) -> CatBondOptimizer:
        """Get an optimizer with the specified risk-free rate.

        Creates a new instance locally — does NOT mutate global state.
        """
        with self._lock:
            if self._returns_df is None:
                raise ValueError("Data not loaded")
            return CatBondOptimizer(self._returns_df.copy(), risk_free_rate=risk_free_rate)


data_store = _DataStore()


def load_data() -> None:
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH, index_col=0)
        data_store.update(df, risk_free_rate=0.0)
    else:
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")


# ============================================================================
# API ENDPOINTS
# ============================================================================

router = APIRouter(prefix="/api/v1")


@router.get("/health", tags=["Health"])
async def health_check():
    df = data_store.returns_df
    return envelope(data={
        "status": "healthy" if df is not None else "degraded",
        "version": "2.0.0",
        "data_loaded": df is not None,
        "data_shape": {"scenarios": df.shape[0], "assets": df.shape[1]} if df is not None else None,
    })


@router.post("/upload", tags=["Data"])
async def upload_data(file: UploadFile = File(...), _auth: bool = Depends(verify_api_key)):
    """
    Upload a CSV file with scenario returns.
    Expected format: First column = scenario index, other columns = asset returns.
    """
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
            raise DataError(info, code=ErrorCode.INVALID_FILE_FORMAT)

        # Validate content type
        allowed_content_types = {
            "text/csv", "application/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "application/octet-stream",  # Common fallback
        }
        if file.content_type and file.content_type not in allowed_content_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported content type: {file.content_type}",
            )

        # Try to read as CSV/Excel
        if file.filename.lower().endswith('.csv'):
            # Respect content type when possible
            df = pd.read_csv(io.BytesIO(contents), index_col=0)
        elif file.filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents), index_col=0)
        else:
            raise DataError("Unsupported file format. Use CSV or Excel.", code=ErrorCode.INVALID_FILE_FORMAT)
        
        # Sanitize column names
        df.columns = sanitize_column_names(df.columns.tolist())

        # Validate data
        if df.empty:
            raise DataError("File is empty", code=ErrorCode.FILE_EMPTY)
        
        # Convert to numeric where possible, but first check for potential CSV/Excel
        # formula injection: any string cell starting with =, +, -, @ should be rejected
        object_cols = df.select_dtypes(include=['object']).columns.tolist()
        if object_cols:
            for col in object_cols:
                # Vectorized check for leading dangerous characters
                series = df[col].astype(str).fillna("")
                if series.str.match(r'^[=+\-@]').any():
                    raise DataError(
                        "File contains potentially dangerous formula cells. Remove leading =, +, - or @ from values.",
                        code=ErrorCode.INVALID_FILE_FORMAT,
                    )

        # Convert to numeric, coerce errors
        df = df.apply(pd.to_numeric, errors='coerce')
        
        # Drop rows/cols with all NaN
        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
        
        if df.shape[1] < 2:
            raise DataError("Need at least 2 assets", code=ErrorCode.INSUFFICIENT_ASSETS)
        
        if df.shape[0] < 100:
            raise DataError("Need at least 100 scenarios", code=ErrorCode.INSUFFICIENT_SCENARIOS)
        
        # Replace in-memory dataset only after validation succeeds
        data_store.update(df, risk_free_rate=0.0)
        
        return envelope(data={
            "status": "success",
            "n_assets": df.shape[1],
            "n_scenarios": df.shape[0],
            "asset_names": list(df.columns),
        })
    except (HTTPException, OptimizerError):
        raise
    except Exception as e:
        logger.exception("File upload processing error")
        raise DataError("Failed to process uploaded file", code=ErrorCode.INVALID_FILE_FORMAT)


@router.post("/reset", tags=["Data"])
async def reset_data(_auth: bool = Depends(verify_api_key)):
    """Reset to default sample data."""
    try:
        load_data()
        logger.info("Data reset to sample data via API reset endpoint")
        return envelope(data={"status": "success", "message": "Reset to sample data"})
    except Exception as e:
        logger.exception("Failed to reset data")
        raise OptimizerError("Internal server error", code=ErrorCode.INTERNAL_ERROR)


@router.get("/assets", tags=["Data"])
async def get_assets():
    returns_df = data_store.returns_df
    if returns_df is None:
        raise DataError("Data not loaded", code=ErrorCode.DATA_NOT_LOADED)
    
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
    
    return envelope(data=[a.model_dump() for a in assets], meta={"count": len(assets)})


@router.post("/optimize", tags=["Portfolio"])
async def optimize_portfolio(request: ValidatedOptimizationRequest, _auth: bool = Depends(verify_api_key)):
    returns_df = data_store.returns_df
    if returns_df is None:
        raise DataError("Data not loaded", code=ErrorCode.DATA_NOT_LOADED)
    
    # Create a LOCAL optimizer — does NOT mutate global state
    opt = data_store.get_optimizer(request.risk_free_rate)
    
    # Run optimization based on method
    method = request.method.lower().replace(" ", "_").replace("(", "").replace(")", "")
    
    if method == "maximum_sharpe_ratio" or method == "max_sharpe":
        result = opt.optimize_max_sharpe(request.min_weight, request.max_weight)
    elif method == "minimum_variance" or method == "min_variance":
        result = opt.optimize_min_variance(request.min_weight, request.max_weight)
    elif method == "minimum_cvar" or method == "min_cvar":
        result = opt.optimize_min_cvar(request.cvar_alpha, request.min_weight, request.max_weight)
    elif method == "mean-cvar_trade-off" or method == "mean_cvar":
        result = opt.optimize_mean_cvar(request.cvar_alpha, request.risk_aversion,
                                        request.min_weight, request.max_weight)
    elif method == "maximum_return_constrained" or method == "max_return":
        if request.constraint_type == "volatility":
            result = opt.optimize_max_return(
                max_volatility=request.max_volatility or 0.15,
                min_weight=request.min_weight, max_weight=request.max_weight
            )
        else:
            result = opt.optimize_max_return(
                max_cvar=request.max_cvar or 0.25,
                alpha=request.cvar_constraint_alpha,
                min_weight=request.min_weight, max_weight=request.max_weight
            )
    elif method == "exponential_utility_cara" or method == "exponential_utility":
        result = opt.optimize_exponential_utility(
            request.exp_risk_aversion, request.min_weight, request.max_weight
        )
    else:
        raise ValidationError(f"Unknown optimization method: {request.method}", code=ErrorCode.INVALID_METHOD)
    
    weights = result["weights"]
    metrics = opt._compute_portfolio_metrics(weights)
    dist_stats = opt._compute_distribution_stats(weights)
    # Use ORIGINAL (unadjusted) returns for consistency with distribution_stats
    original_portfolio_returns = opt.original_returns_matrix @ weights
    portfolio_returns = original_portfolio_returns.tolist()
    
    # Find the best scenario (highest portfolio return) and get each asset's return in that scenario
    best_scenario_idx = int(np.argmax(original_portfolio_returns))
    best_scenario_asset_returns = opt.original_returns_matrix[best_scenario_idx, :]
    best_scenario_returns = {asset: float(r) for asset, r in zip(opt.assets, best_scenario_asset_returns)}
    
    # Find VaR scenarios (sorted indices, find the scenario at each percentile)
    sorted_indices = np.argsort(original_portfolio_returns)
    n_scenarios = len(original_portfolio_returns)
    var90_idx = sorted_indices[int(n_scenarios * 0.10)]  # 10th percentile
    var95_idx = sorted_indices[int(n_scenarios * 0.05)]  # 5th percentile
    var99_idx = sorted_indices[int(n_scenarios * 0.01)]  # 1st percentile
    
    var90_scenario_returns = {asset: float(r) for asset, r in zip(opt.assets, opt.original_returns_matrix[var90_idx, :])}
    var95_scenario_returns = {asset: float(r) for asset, r in zip(opt.assets, opt.original_returns_matrix[var95_idx, :])}
    var99_scenario_returns = {asset: float(r) for asset, r in zip(opt.assets, opt.original_returns_matrix[var99_idx, :])}
    
    # Mean returns for each asset (for expected loss calculation)
    asset_mean_returns = {asset: float(r) for asset, r in zip(opt.assets, opt.original_returns_matrix.mean(axis=0))}
    
    response_dict = OptimizationResponse(
        status=result["status"],
        method=result["method"],
        weights={asset: float(w) for asset, w in zip(opt.assets, weights)},
        metrics=metrics,
        portfolio_returns=portfolio_returns,
        distribution_stats=dist_stats,
        best_scenario_returns=best_scenario_returns,
        var90_scenario_returns=var90_scenario_returns,
        var95_scenario_returns=var95_scenario_returns,
        var99_scenario_returns=var99_scenario_returns,
        asset_mean_returns=asset_mean_returns,
    ).model_dump()
    return envelope(data=response_dict)


@router.get("/efficient-frontier", tags=["Portfolio"])
async def get_efficient_frontier(
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    n_points: int = Query(20, ge=5, le=100),  # Bounded to prevent DoS
    risk_free_rate: float = 0.0
):
    if data_store.returns_df is None:
        raise DataError("Data not loaded", code=ErrorCode.DATA_NOT_LOADED)
    
    # Create optimizer with requested risk-free rate
    frontier_optimizer = data_store.get_optimizer(risk_free_rate)
    frontier = frontier_optimizer.efficient_frontier(n_points, min_weight, max_weight)
    return envelope(data=frontier, meta={"n_points": len(frontier)})


@router.get("/scenarios", tags=["Data"])
async def get_scenarios(sample_size: int = 1000):
    """Get a sample of scenario returns for visualization."""
    returns_df = data_store.returns_df
    if returns_df is None:
        raise DataError("Data not loaded", code=ErrorCode.DATA_NOT_LOADED)
    
    # Sample scenarios
    n = len(returns_df)
    indices = np.linspace(0, n - 1, min(sample_size, n), dtype=int)
    
    return envelope(data={
        "scenarios": indices.tolist(),
        "n_total": n,
        "assets": returns_df.columns.tolist(),
    })

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    # Bind to a safe default host/port unless overridden in environment
    uvicorn.run(app, host=BIND_HOST, port=BIND_PORT)
