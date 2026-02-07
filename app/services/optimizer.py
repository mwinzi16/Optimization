"""Unified CatBondOptimizer — core optimization engine."""

from __future__ import annotations

from typing import Dict, List, Optional

import cvxpy as cp
import numpy as np
import pandas as pd
from scipy.optimize import minimize


class CatBondOptimizer:
    """Portfolio optimizer for catastrophe bond and ILS portfolios.
    
    Implements multiple optimization strategies using scenario-based
    returns data. Supports convex optimization via CVXPY for tractable
    problems and SciPy SLSQP for non-convex utility maximization.
    """
    
    def __init__(self, returns_df: pd.DataFrame, risk_free_rate: float = 0.0) -> None:
        self.rf = risk_free_rate
        self.original_returns_matrix = returns_df.values
        adjusted_returns = returns_df - risk_free_rate
        self.returns = adjusted_returns
        self.assets = list(returns_df.columns)
        self.n_assets = len(self.assets)
        self.n_scenarios = len(returns_df)
        self.mean_returns = adjusted_returns.mean().values
        self.cov_matrix = adjusted_returns.cov().values
        self.returns_matrix = adjusted_returns.values
        
        eigenvalues = np.linalg.eigvalsh(self.cov_matrix)
        if eigenvalues.min() < 1e-10:
            self.cov_matrix += np.eye(self.n_assets) * 1e-8
        
        self.asset_max_returns = adjusted_returns.max().values
    
    def _compute_portfolio_metrics(self, weights: np.ndarray) -> dict:
        """Compute comprehensive risk and return metrics."""
        port_returns = self.original_returns_matrix @ weights
        exp_return = float(np.mean(port_returns))
        volatility = float(np.std(port_returns))
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
            "var_90": var_90, "var_95": var_95, "var_98": var_98, "var_99": var_99,
            "cvar_90": cvar_90, "cvar_95": cvar_95, "cvar_98": cvar_98, "cvar_99": cvar_99,
            "worst_scenario": worst_scenario,
        }
    
    def _compute_distribution_stats(self, weights: np.ndarray) -> dict:
        """Compute detailed distribution statistics for portfolio returns."""
        port_returns = self.original_returns_matrix @ weights
        no_loss_return = float(np.max(port_returns))
        mean_return = float(np.mean(port_returns))
        expected_loss = mean_return - no_loss_return
        
        return {
            "mean": mean_return, "median": float(np.median(port_returns)),
            "std": float(np.std(port_returns)),
            "skewness": float(pd.Series(port_returns).skew()),
            "kurtosis": float(pd.Series(port_returns).kurtosis()),
            "min": float(np.min(port_returns)), "max": float(np.max(port_returns)),
            "expected_loss": expected_loss, "no_loss_return": no_loss_return,
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
    
    def get_equal_weight_metrics(self) -> dict:
        """Compute metrics for an equal-weight benchmark portfolio."""
        weights = np.ones(self.n_assets) / self.n_assets
        metrics = self._compute_portfolio_metrics(weights)
        metrics["portfolio_returns"] = (self.original_returns_matrix @ weights).tolist()
        return metrics
    
    def optimize_max_sharpe(self, min_weight: float = 0.0, max_weight: float = 1.0) -> dict:
        if np.all(self.mean_returns <= 0):
            return self.optimize_min_variance(min_weight, max_weight)
        y = cp.Variable(self.n_assets)
        portfolio_var = cp.quad_form(y, self.cov_matrix)
        constraints = [self.mean_returns @ y == 1, y >= 0]
        if min_weight > 0:
            constraints.append(y >= min_weight * cp.sum(y))
        if max_weight < 1:
            constraints.append(y <= max_weight * cp.sum(y))
        problem = cp.Problem(cp.Minimize(portfolio_var), constraints)
        problem.solve(solver=cp.CLARABEL)
        if problem.status != "optimal" or y.value is None or np.sum(y.value) <= 0:
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"fallback: {problem.status}"
        else:
            y_vals = np.maximum(y.value, 0)
            weights = y_vals / np.sum(y_vals)
            status = "optimal"
        return {"weights": weights, "status": status, "method": "max_sharpe"}
    
    def optimize_min_variance(self, min_weight: float = 0.0, max_weight: float = 1.0,
                               target_return: float = None) -> dict:
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
        w = cp.Variable(self.n_assets)
        constraints = [cp.sum(w) == 1, w >= min_weight, w <= max_weight]
        if max_volatility is not None:
            portfolio_var = cp.quad_form(w, self.cov_matrix)
            constraints.append(portfolio_var <= max_volatility ** 2)
        if max_cvar is not None:
            z = cp.Variable()
            u = cp.Variable(self.n_scenarios)
            port_returns_orig = self.original_returns_matrix @ w
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
        scale = 50
        C = (risk_aversion - 0.5) * 2
        if abs(C) < 1e-6:
            def negative_expected_return(weights):
                return -np.mean(self.returns_matrix @ weights)
            def gradient(weights):
                return -np.mean(self.returns_matrix, axis=0)
            constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
            bounds = [(min_weight, max_weight) for _ in range(self.n_assets)]
            w0 = np.ones(self.n_assets) / self.n_assets
            result = minimize(negative_expected_return, w0, method="SLSQP", jac=gradient,
                            bounds=bounds, constraints=constraints, options={"ftol": 1e-10, "maxiter": 1000})
        else:
            def negative_expected_value(weights):
                port_returns = self.returns_matrix @ weights
                exponents = np.clip(-C * scale * port_returns, -500, 500)
                exp_terms = np.exp(exponents)
                if C > 0:
                    return float(np.mean(exp_terms))
                else:
                    return float(-np.mean(exp_terms))
            def gradient(weights):
                port_returns = self.returns_matrix @ weights
                exponents = np.clip(-C * scale * port_returns, -500, 500)
                exp_terms = np.exp(exponents)
                grad = np.mean(-C * scale * self.returns_matrix * exp_terms[:, np.newaxis], axis=0)
                if C > 0:
                    return grad
                else:
                    return -grad
            constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
            bounds = [(min_weight, max_weight) for _ in range(self.n_assets)]
            w0 = np.ones(self.n_assets) / self.n_assets
            result = minimize(negative_expected_value, w0, method="SLSQP", jac=gradient,
                            bounds=bounds, constraints=constraints, options={"ftol": 1e-10, "maxiter": 1000})
        if result.success:
            weights = result.x / result.x.sum()
            status = "optimal"
        else:
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"fallback: {result.message}"
        return {"weights": weights, "status": status, "method": f"exponential_utility_C_{C:.2f}"}
    
    def efficient_frontier(self, n_points: int = 20, min_weight: float = 0.0,
                           max_weight: float = 1.0) -> list[dict]:
        min_var_result = self.optimize_min_variance(min_weight, max_weight)
        min_var_metrics = self._compute_portfolio_metrics(min_var_result["weights"])
        max_return = float(self.mean_returns.max())
        min_return = min_var_metrics["expected_return"] - self.rf
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
