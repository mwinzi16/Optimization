"""
Cat Bond Portfolio Optimizer

Supports multiple optimization objectives:
- Maximum Return (for given risk)
- Minimum Risk (for given return)
- Maximum Sharpe Ratio
- Minimum CVaR (Conditional Value at Risk)
- Mean-CVaR optimization

Uses scenario-based returns as input.
"""

import numpy as np
import pandas as pd
import cvxpy as cp
from pathlib import Path
from dataclasses import dataclass
from typing import Literal


@dataclass
class OptimizationResult:
    """Container for optimization results."""
    weights: pd.Series
    expected_return: float
    volatility: float
    sharpe_ratio: float
    var_95: float
    cvar_95: float
    var_99: float
    cvar_99: float
    max_drawdown: float
    objective: str
    status: str


class CatBondOptimizer:
    """
    Portfolio optimizer for cat bond portfolios using scenario-based returns.
    """
    
    def __init__(self, returns_df: pd.DataFrame, risk_free_rate: float = 0.04):
        """
        Initialize optimizer with scenario returns.
        
        Args:
            returns_df: DataFrame with scenarios as rows, assets as columns.
                       Values are total returns (e.g., 0.08 = 8% return, -1.0 = total loss)
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation
        """
        self.returns = returns_df
        self.assets = list(returns_df.columns)
        self.n_assets = len(self.assets)
        self.n_scenarios = len(returns_df)
        self.rf = risk_free_rate
        
        # Precompute statistics
        self.mean_returns = returns_df.mean().values
        self.cov_matrix = returns_df.cov().values
        self.returns_matrix = returns_df.values
        
    def _compute_portfolio_metrics(self, weights: np.ndarray) -> dict:
        """Compute all portfolio metrics for given weights."""
        # Portfolio returns per scenario
        port_returns = self.returns_matrix @ weights
        
        # Basic stats
        exp_return = np.mean(port_returns)
        volatility = np.std(port_returns)
        sharpe = (exp_return - self.rf) / volatility if volatility > 0 else 0
        
        # VaR and CVaR at different confidence levels
        var_95 = np.percentile(port_returns, 5)
        var_99 = np.percentile(port_returns, 1)
        cvar_95 = port_returns[port_returns <= var_95].mean() if (port_returns <= var_95).any() else var_95
        cvar_99 = port_returns[port_returns <= var_99].mean() if (port_returns <= var_99).any() else var_99
        
        # Max drawdown (simplified - worst single period)
        max_drawdown = port_returns.min()
        
        return {
            "expected_return": exp_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "var_99": var_99,
            "cvar_99": cvar_99,
            "max_drawdown": max_drawdown,
        }
    
    def optimize_max_sharpe(
        self,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        long_only: bool = True,
    ) -> OptimizationResult:
        """
        Find the portfolio that maximizes the Sharpe ratio.
        
        Uses the Cornuejols-Tutuncu transformation for convex optimization:
        1. Define y = w/k where k is a scaling factor
        2. Set constraint: excess_returns @ y = 1 (fixes the excess return)
        3. Minimize y'Σy (variance in transformed space)
        4. Recover weights: w = y / sum(y)
        
        This transforms the non-convex Sharpe maximization into a convex QP.
        """
        # Expected excess returns
        excess_returns = self.mean_returns - self.rf
        
        # Check if we have positive excess returns to maximize
        if np.all(excess_returns <= 0):
            # Fall back to minimum variance if no positive excess returns
            return self.optimize_min_variance(min_weight, max_weight)
        
        y = cp.Variable(self.n_assets)
        
        # Objective: minimize variance in transformed space
        portfolio_var = cp.quad_form(y, self.cov_matrix)
        
        # Key constraint: fix excess return to 1 (the transformation trick)
        constraints = [
            excess_returns @ y == 1,  # This is the Sharpe transformation
        ]
        
        if long_only:
            constraints.append(y >= 0)
        
        problem = cp.Problem(cp.Minimize(portfolio_var), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal" or y.value is None or np.sum(y.value) <= 0:
            # Fallback: equal weight
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback to equal weight: {problem.status}"
        else:
            # Normalize y to get actual portfolio weights
            y_vals = np.maximum(y.value, 0) if long_only else y.value
            weights = y_vals / np.sum(y_vals)
            
            # Apply min/max weight constraints via post-processing if needed
            if min_weight > 0 or max_weight < 1:
                weights = np.clip(weights, min_weight, max_weight)
                weights = weights / np.sum(weights)  # Re-normalize
            
            status = "optimal"
        
        metrics = self._compute_portfolio_metrics(weights)
        
        return OptimizationResult(
            weights=pd.Series(weights, index=self.assets),
            objective="max_sharpe",
            status=status,
            **metrics
        )
    
    def optimize_min_variance(
        self,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        target_return: float = None,
    ) -> OptimizationResult:
        """
        Find the minimum variance portfolio, optionally with a target return.
        """
        w = cp.Variable(self.n_assets)
        
        # Objective: minimize portfolio variance
        portfolio_var = cp.quad_form(w, self.cov_matrix)
        
        constraints = [
            cp.sum(w) == 1,
            w >= min_weight,
            w <= max_weight,
        ]
        
        if target_return is not None:
            constraints.append(self.mean_returns @ w >= target_return)
        
        problem = cp.Problem(cp.Minimize(portfolio_var), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback to equal weight: {problem.status}"
        else:
            weights = w.value
            status = "optimal"
        
        metrics = self._compute_portfolio_metrics(weights)
        
        return OptimizationResult(
            weights=pd.Series(weights, index=self.assets),
            objective="min_variance" + (f"_target_{target_return:.1%}" if target_return else ""),
            status=status,
            **metrics
        )
    
    def optimize_min_cvar(
        self,
        alpha: float = 0.05,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
        target_return: float = None,
    ) -> OptimizationResult:
        """
        Minimize Conditional Value at Risk (CVaR / Expected Shortfall).
        
        Args:
            alpha: Confidence level (0.05 = 95% CVaR, 0.01 = 99% CVaR)
            target_return: Optional minimum expected return constraint
        """
        w = cp.Variable(self.n_assets)
        z = cp.Variable()  # VaR threshold
        u = cp.Variable(self.n_scenarios)  # Auxiliary variables for CVaR
        
        # Portfolio returns for each scenario
        port_returns = self.returns_matrix @ w
        
        # CVaR formulation (Rockafellar & Uryasev)
        # CVaR = z + (1/alpha) * E[max(-r - z, 0)]
        objective = z + (1 / (alpha * self.n_scenarios)) * cp.sum(u)
        
        constraints = [
            cp.sum(w) == 1,
            w >= min_weight,
            w <= max_weight,
            u >= 0,
            u >= -port_returns - z,  # u_i >= max(-r_i - z, 0)
        ]
        
        if target_return is not None:
            constraints.append(self.mean_returns @ w >= target_return)
        
        problem = cp.Problem(cp.Minimize(objective), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback to equal weight: {problem.status}"
        else:
            weights = w.value
            status = "optimal"
        
        metrics = self._compute_portfolio_metrics(weights)
        
        return OptimizationResult(
            weights=pd.Series(weights, index=self.assets),
            objective=f"min_cvar_{int((1-alpha)*100)}",
            status=status,
            **metrics
        )
    
    def optimize_mean_cvar(
        self,
        alpha: float = 0.05,
        risk_aversion: float = 1.0,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
    ) -> OptimizationResult:
        """
        Optimize mean - risk_aversion * CVaR trade-off.
        
        Args:
            alpha: CVaR confidence level
            risk_aversion: Lambda parameter (higher = more risk averse)
        """
        w = cp.Variable(self.n_assets)
        z = cp.Variable()
        u = cp.Variable(self.n_scenarios)
        
        port_returns = self.returns_matrix @ w
        
        # Expected return
        exp_return = self.mean_returns @ w
        
        # CVaR component
        cvar = z + (1 / (alpha * self.n_scenarios)) * cp.sum(u)
        
        # Objective: maximize return - lambda * CVaR
        # Equivalent to minimize: -return + lambda * CVaR
        objective = -exp_return + risk_aversion * cvar
        
        constraints = [
            cp.sum(w) == 1,
            w >= min_weight,
            w <= max_weight,
            u >= 0,
            u >= -port_returns - z,
        ]
        
        problem = cp.Problem(cp.Minimize(objective), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback to equal weight: {problem.status}"
        else:
            weights = w.value
            status = "optimal"
        
        metrics = self._compute_portfolio_metrics(weights)
        
        return OptimizationResult(
            weights=pd.Series(weights, index=self.assets),
            objective=f"mean_cvar_lambda_{risk_aversion}",
            status=status,
            **metrics
        )
    
    def optimize_max_return(
        self,
        max_volatility: float = None,
        max_cvar: float = None,
        alpha: float = 0.05,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
    ) -> OptimizationResult:
        """
        Maximize expected return subject to risk constraints.
        
        Args:
            max_volatility: Maximum allowed portfolio volatility
            max_cvar: Maximum allowed CVaR (as positive number, e.g., 0.2 = -20% loss)
            alpha: CVaR confidence level
        """
        w = cp.Variable(self.n_assets)
        
        constraints = [
            cp.sum(w) == 1,
            w >= min_weight,
            w <= max_weight,
        ]
        
        # Volatility constraint
        if max_volatility is not None:
            portfolio_var = cp.quad_form(w, self.cov_matrix)
            constraints.append(portfolio_var <= max_volatility ** 2)
        
        # CVaR constraint
        if max_cvar is not None:
            z = cp.Variable()
            u = cp.Variable(self.n_scenarios)
            port_returns = self.returns_matrix @ w
            cvar = z + (1 / (alpha * self.n_scenarios)) * cp.sum(u)
            constraints.extend([
                u >= 0,
                u >= -port_returns - z,
                cvar <= max_cvar,  # CVaR (as loss) should be less than max
            ])
        
        # Objective: maximize expected return
        objective = -self.mean_returns @ w  # Minimize negative return
        
        problem = cp.Problem(cp.Minimize(objective), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback to equal weight: {problem.status}"
        else:
            weights = w.value
            status = "optimal"
        
        metrics = self._compute_portfolio_metrics(weights)
        
        return OptimizationResult(
            weights=pd.Series(weights, index=self.assets),
            objective="max_return",
            status=status,
            **metrics
        )
    
    def optimize_exponential_utility(
        self,
        risk_aversion: float = 0.5,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
    ) -> OptimizationResult:
        """
        Maximize expected exponential utility (CARA utility function).
        
        Based on Elton/Gruber "Modern Portfolio Theory and Investment Analysis" Chapter 10.
        Utility function: U(W) = -e^(-C*W)
        
        For portfolio returns: U = -e^(-C * 50 * return) / C
        
        We maximize: E[U] = -(1/C) * E[e^(-C * 50 * r)]
        Equivalent to minimizing: E[e^(-C * 50 * r)]
        
        Args:
            risk_aversion: C parameter (0 < C <= 1). Higher = more risk averse.
                          C near 0 = nearly risk neutral (maximize return)
                          C = 1 = highly risk averse
            min_weight: Minimum weight per asset
            max_weight: Maximum weight per asset
        """
        from scipy.optimize import minimize
        
        # Scale factor as per Elton/Gruber formulation
        scale = 50
        
        def negative_expected_utility(weights):
            """Compute negative expected utility (we minimize this)."""
            port_returns = self.returns_matrix @ weights
            # U = -e^(-C * scale * r) / C
            # E[U] = -(1/C) * mean(e^(-C * scale * r))
            # Minimize: mean(e^(-C * scale * r))
            utilities = np.exp(-risk_aversion * scale * port_returns)
            return np.mean(utilities)
        
        def gradient(weights):
            """Compute gradient of the objective."""
            port_returns = self.returns_matrix @ weights
            exp_terms = np.exp(-risk_aversion * scale * port_returns)
            # d/dw = mean(-C * scale * r_i * e^(-C*scale*r)) for each asset
            grad = np.zeros(self.n_assets)
            for i in range(self.n_assets):
                grad[i] = np.mean(-risk_aversion * scale * self.returns_matrix[:, i] * exp_terms)
            return grad
        
        # Constraints
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1}  # Weights sum to 1
        ]
        
        # Bounds
        bounds = [(min_weight, max_weight) for _ in range(self.n_assets)]
        
        # Initial guess: equal weight
        w0 = np.ones(self.n_assets) / self.n_assets
        
        # Optimize
        result = minimize(
            negative_expected_utility,
            w0,
            method="SLSQP",
            jac=gradient,
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-10, "maxiter": 1000}
        )
        
        if result.success:
            weights = result.x
            # Ensure weights are normalized (numerical precision)
            weights = weights / weights.sum()
            status = "optimal"
        else:
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback to equal weight: {result.message}"
        
        metrics = self._compute_portfolio_metrics(weights)
        
        # Add expected utility to metrics
        port_returns = self.returns_matrix @ weights
        expected_utility = -np.mean(np.exp(-risk_aversion * scale * port_returns)) / risk_aversion
        metrics["expected_utility"] = expected_utility
        
        return OptimizationResult(
            weights=pd.Series(weights, index=self.assets),
            objective=f"exponential_utility_C_{risk_aversion}",
            status=status,
            **metrics
        )
    
    def efficient_frontier(
        self,
        n_points: int = 20,
        min_weight: float = 0.0,
        max_weight: float = 1.0,
    ) -> pd.DataFrame:
        """
        Compute the efficient frontier.
        
        Returns DataFrame with portfolios from min variance to max return.
        """
        # Get min variance and max return portfolios
        min_var_result = self.optimize_min_variance(min_weight, max_weight)
        
        # Max return = 100% in highest return asset
        max_return = self.mean_returns.max()
        min_return = min_var_result.expected_return
        
        target_returns = np.linspace(min_return, max_return * 0.95, n_points)
        
        frontier_data = []
        
        for target in target_returns:
            result = self.optimize_min_variance(min_weight, max_weight, target_return=target)
            if result.status == "optimal":
                frontier_data.append({
                    "target_return": target,
                    "expected_return": result.expected_return,
                    "volatility": result.volatility,
                    "sharpe_ratio": result.sharpe_ratio,
                    "cvar_95": result.cvar_95,
                    "cvar_99": result.cvar_99,
                    **{f"w_{asset}": result.weights[asset] for asset in self.assets}
                })
        
        return pd.DataFrame(frontier_data)


def format_result(result: OptimizationResult) -> str:
    """Format optimization result for display."""
    lines = [
        f"\n{'='*60}",
        f"OPTIMIZATION RESULT: {result.objective.upper()}",
        f"Status: {result.status}",
        f"{'='*60}",
        f"\nPORTFOLIO WEIGHTS:",
    ]
    
    for asset, weight in result.weights.items():
        lines.append(f"  {asset}: {weight:>8.2%}")
    
    lines.extend([
        f"\nPORTFOLIO METRICS:",
        f"  Expected Return:  {result.expected_return:>8.2%}",
        f"  Volatility:       {result.volatility:>8.2%}",
        f"  Sharpe Ratio:     {result.sharpe_ratio:>8.2f}",
        f"  VaR 95%:          {result.var_95:>8.2%}",
        f"  CVaR 95%:         {result.cvar_95:>8.2%}",
        f"  VaR 99%:          {result.var_99:>8.2%}",
        f"  CVaR 99%:         {result.cvar_99:>8.2%}",
        f"  Max Drawdown:     {result.max_drawdown:>8.2%}",
    ])
    
    return "\n".join(lines)


def main():
    """Example usage with generated sample data."""
    # Load data
    data_path = Path(__file__).parent / "data" / "scenario_returns.csv"
    print(f"Loading scenario data from: {data_path}")
    
    returns_df = pd.read_csv(data_path, index_col=0)
    print(f"Loaded {len(returns_df):,} scenarios for {len(returns_df.columns)} assets\n")
    
    # Initialize optimizer
    optimizer = CatBondOptimizer(returns_df, risk_free_rate=0.04)
    
    # Run different optimizations
    print("\n" + "#"*60)
    print("# RUNNING PORTFOLIO OPTIMIZATIONS")
    print("#"*60)
    
    # 1. Maximum Sharpe Ratio
    result_sharpe = optimizer.optimize_max_sharpe()
    print(format_result(result_sharpe))
    
    # 2. Minimum Variance
    result_minvar = optimizer.optimize_min_variance()
    print(format_result(result_minvar))
    
    # 3. Minimum CVaR 95%
    result_mincvar = optimizer.optimize_min_cvar(alpha=0.05)
    print(format_result(result_mincvar))
    
    # 4. Mean-CVaR with different risk aversions
    for lambda_val in [0.5, 1.0, 2.0]:
        result_mean_cvar = optimizer.optimize_mean_cvar(risk_aversion=lambda_val)
        print(format_result(result_mean_cvar))
    
    # 5. Max return with volatility constraint
    result_maxret = optimizer.optimize_max_return(max_volatility=0.10)
    print(format_result(result_maxret))
    
    # 6. Equal weight benchmark
    equal_weights = np.ones(optimizer.n_assets) / optimizer.n_assets
    metrics = optimizer._compute_portfolio_metrics(equal_weights)
    print(f"\n{'='*60}")
    print("BENCHMARK: EQUAL WEIGHT PORTFOLIO")
    print(f"{'='*60}")
    print(f"\n  Expected Return:  {metrics['expected_return']:>8.2%}")
    print(f"  Volatility:       {metrics['volatility']:>8.2%}")
    print(f"  Sharpe Ratio:     {metrics['sharpe_ratio']:>8.2f}")
    print(f"  CVaR 95%:         {metrics['cvar_95']:>8.2%}")
    print(f"  CVaR 99%:         {metrics['cvar_99']:>8.2%}")
    
    # Efficient Frontier
    print(f"\n{'='*60}")
    print("EFFICIENT FRONTIER (sample points)")
    print(f"{'='*60}")
    frontier = optimizer.efficient_frontier(n_points=10)
    print(frontier[["expected_return", "volatility", "sharpe_ratio", "cvar_95"]].to_string())


if __name__ == "__main__":
    main()
