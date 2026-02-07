"""
Cat Bond Portfolio Optimizer - Streamlit Application

A state-of-the-art portfolio optimization tool for catastrophe bonds
with interactive visualizations and comprehensive risk analytics.
"""

from __future__ import annotations

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import cvxpy as cp
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

# Page configuration
st.set_page_config(
    page_title="Cat Bond Portfolio Optimizer",
    page_icon="🌪️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for sleek UI
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e3a5f;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #6c757d;
        margin-top: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-positive { color: #28a745 !important; }
    .metric-negative { color: #dc3545 !important; }
    .metric-neutral { color: #1e3a5f !important; }
    
    /* Section headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #1e3a5f;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e9ecef;
    }
    
    /* Stats table */
    .stats-table {
        width: 100%;
        border-collapse: collapse;
    }
    
    .stats-table td {
        padding: 0.6rem 0.8rem;
        border-bottom: 1px solid #e9ecef;
    }
    
    .stats-table tr:last-child td {
        border-bottom: none;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stNumberInput label {
        font-weight: 500;
        color: #1e3a5f;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 500;
        width: 100%;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2d5a87 0%, #3d6a97 100%);
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: #1e3a5f;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1e3a5f;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# OPTIMIZER CLASS (embedded for standalone app)
# ============================================================================

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
    worst_scenario: float
    objective: str
    status: str
    portfolio_returns: np.ndarray = None


class CatBondOptimizer:
    """Portfolio optimizer for cat bond portfolios using scenario-based returns."""
    
    def __init__(self, returns_df: pd.DataFrame, risk_free_rate: float = 0.04):
        self.returns = returns_df
        self.assets = list(returns_df.columns)
        self.n_assets = len(self.assets)
        self.n_scenarios = len(returns_df)
        self.rf = risk_free_rate
        
        self.mean_returns = returns_df.mean().values
        self.cov_matrix = returns_df.cov().values
        
        # Ensure covariance matrix is positive semi-definite
        eigenvalues = np.linalg.eigvalsh(self.cov_matrix)
        if eigenvalues.min() < 1e-10:
            self.cov_matrix += np.eye(self.n_assets) * 1e-8
        
        self.returns_matrix = returns_df.values
        
    def _compute_portfolio_metrics(self, weights: np.ndarray) -> dict:
        port_returns = self.returns_matrix @ weights
        
        exp_return = np.mean(port_returns)
        volatility = np.std(port_returns, ddof=1)
        sharpe = (exp_return - self.rf) / volatility if volatility > 0 else 0
        
        var_95 = np.percentile(port_returns, 5)
        var_99 = np.percentile(port_returns, 1)
        cvar_95 = port_returns[port_returns <= var_95].mean() if (port_returns <= var_95).any() else var_95
        cvar_99 = port_returns[port_returns <= var_99].mean() if (port_returns <= var_99).any() else var_99
        
        worst_scenario = port_returns.min()
        
        return {
            "expected_return": exp_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "var_99": var_99,
            "cvar_99": cvar_99,
            "worst_scenario": worst_scenario,
            "portfolio_returns": port_returns,
        }
    
    def optimize_max_sharpe(self, min_weight: float = 0.0, max_weight: float = 1.0) -> OptimizationResult:
        """
        Maximize Sharpe Ratio using the transformation method.
        
        Solves: min y'Σy  s.t. (μ - rf)'y = 1, y >= 0
        Then normalizes: w = y / sum(y)
        
        This is the Cornish-Fisher tangency portfolio approach.
        Weight constraints are enforced in the transformed space.
        """
        excess_returns = self.mean_returns - self.rf
        
        # If all excess returns are non-positive, fall back to min variance
        if np.all(excess_returns <= 0):
            return self.optimize_min_variance(min_weight, max_weight)
        
        y = cp.Variable(self.n_assets)
        portfolio_var = cp.quad_form(y, self.cov_matrix)
        
        # Sharpe transformation: fix excess return = 1, minimize variance
        constraints = [
            excess_returns @ y == 1,  # Key transformation constraint
            y >= 0,
        ]
        
        # Weight constraints in transformed space: w_i = y_i / sum(y)
        # w_i >= min_weight  ⟺  y_i >= min_weight * sum(y)
        # w_i <= max_weight  ⟺  y_i <= max_weight * sum(y)
        if min_weight > 0:
            constraints.append(y >= min_weight * cp.sum(y))
        if max_weight < 1:
            constraints.append(y <= max_weight * cp.sum(y))
        
        problem = cp.Problem(cp.Minimize(portfolio_var), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal" or y.value is None or np.sum(y.value) <= 0:
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback: {problem.status}"
        else:
            y_vals = np.maximum(y.value, 0)
            weights = y_vals / np.sum(y_vals)
            status = "optimal"
        
        metrics = self._compute_portfolio_metrics(weights)
        
        return OptimizationResult(
            weights=pd.Series(weights, index=self.assets),
            objective="max_sharpe",
            status=status,
            **metrics
        )
    
    def optimize_min_variance(self, min_weight: float = 0.0, max_weight: float = 1.0, 
                              target_return: float = None) -> OptimizationResult:
        w = cp.Variable(self.n_assets)
        portfolio_var = cp.quad_form(w, self.cov_matrix)
        
        constraints = [cp.sum(w) == 1, w >= min_weight, w <= max_weight]
        
        if target_return is not None:
            constraints.append(self.mean_returns @ w >= target_return)
        
        problem = cp.Problem(cp.Minimize(portfolio_var), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback: {problem.status}"
        else:
            weights = w.value
            status = "optimal"
        
        metrics = self._compute_portfolio_metrics(weights)
        
        return OptimizationResult(
            weights=pd.Series(weights, index=self.assets),
            objective="min_variance",
            status=status,
            **metrics
        )
    
    def optimize_min_cvar(self, alpha: float = 0.05, min_weight: float = 0.0,
                          max_weight: float = 1.0, target_return: float = None) -> OptimizationResult:
        w = cp.Variable(self.n_assets)
        z = cp.Variable()
        u = cp.Variable(self.n_scenarios)
        
        port_returns = self.returns_matrix @ w
        objective = z + (1 / (alpha * self.n_scenarios)) * cp.sum(u)
        
        constraints = [
            cp.sum(w) == 1, w >= min_weight, w <= max_weight,
            u >= 0, u >= -port_returns - z,
        ]
        
        if target_return is not None:
            constraints.append(self.mean_returns @ w >= target_return)
        
        problem = cp.Problem(cp.Minimize(objective), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback: {problem.status}"
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
    
    def optimize_mean_cvar(self, alpha: float = 0.05, risk_aversion: float = 1.0,
                           min_weight: float = 0.0, max_weight: float = 1.0) -> OptimizationResult:
        w = cp.Variable(self.n_assets)
        z = cp.Variable()
        u = cp.Variable(self.n_scenarios)
        
        port_returns = self.returns_matrix @ w
        exp_return = self.mean_returns @ w
        cvar = z + (1 / (alpha * self.n_scenarios)) * cp.sum(u)
        
        objective = -exp_return + risk_aversion * cvar
        
        constraints = [
            cp.sum(w) == 1, w >= min_weight, w <= max_weight,
            u >= 0, u >= -port_returns - z,
        ]
        
        problem = cp.Problem(cp.Minimize(objective), constraints)
        problem.solve(solver=cp.CLARABEL)
        
        if problem.status != "optimal":
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback: {problem.status}"
        else:
            weights = w.value
            status = "optimal"
        
        metrics = self._compute_portfolio_metrics(weights)
        
        return OptimizationResult(
            weights=pd.Series(weights, index=self.assets),
            objective=f"mean_cvar_λ{risk_aversion}",
            status=status,
            **metrics
        )
    
    def optimize_max_return(self, max_volatility: float = None, max_cvar: float = None,
                            alpha: float = 0.05, min_weight: float = 0.0,
                            max_weight: float = 1.0) -> OptimizationResult:
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
            status = f"Fallback: {problem.status}"
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
    
    def optimize_exponential_utility(self, risk_aversion: float = 0.5,
                                      min_weight: float = 0.0, 
                                      max_weight: float = 1.0) -> OptimizationResult:
        """
        Maximize expected exponential utility (CARA utility function).
        
        Based on Elton/Gruber "Modern Portfolio Theory and Investment Analysis" Chapter 10.
        Utility function: U(W) = -e^(-C*W)
        
        For portfolio returns: V = -e^(-C * 50 * return) / C
        
        We maximize: E[U] = -(1/C) * E[e^(-C * 50 * r)]
        Equivalent to minimizing: E[e^(-C * 50 * r)]
        
        Args:
            risk_aversion: C parameter (0 < C <= 1). Higher = more risk averse.
                          C near 0 = nearly risk neutral (maximize return)
                          C = 1 = highly risk averse
        """
        from scipy.optimize import minimize
        
        scale = 50  # Scaling factor per Elton/Gruber formulation
        
        def negative_expected_utility(weights):
            port_returns = self.returns_matrix @ weights
            exponents = np.clip(-risk_aversion * scale * port_returns, -500, 500)
            utilities = np.exp(exponents)
            return np.mean(utilities)
        
        def gradient(weights):
            port_returns = self.returns_matrix @ weights
            exponents = np.clip(-risk_aversion * scale * port_returns, -500, 500)
            exp_terms = np.exp(exponents)
            # Vectorized gradient
            return np.mean(-risk_aversion * scale * self.returns_matrix * exp_terms[:, np.newaxis], axis=0)
        
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(min_weight, max_weight) for _ in range(self.n_assets)]
        w0 = np.ones(self.n_assets) / self.n_assets
        
        opt_result = minimize(
            negative_expected_utility, w0,
            method="SLSQP", jac=gradient,
            bounds=bounds, constraints=constraints,
            options={"ftol": 1e-10, "maxiter": 1000}
        )
        
        if opt_result.success:
            weights = opt_result.x / opt_result.x.sum()
            status = "optimal"
        else:
            weights = np.ones(self.n_assets) / self.n_assets
            status = f"Fallback: {opt_result.message}"
        
        metrics = self._compute_portfolio_metrics(weights)
        
        # Compute expected utility for display
        port_returns = self.returns_matrix @ weights
        exponents = np.clip(-risk_aversion * scale * port_returns, -500, 500)
        expected_utility = -np.mean(np.exp(exponents)) / risk_aversion
        metrics["expected_utility"] = expected_utility
        
        return OptimizationResult(
            weights=pd.Series(weights, index=self.assets),
            objective=f"exponential_utility_C_{risk_aversion}",
            status=status,
            **metrics
        )
    
    def efficient_frontier(self, n_points: int = 25, min_weight: float = 0.0,
                           max_weight: float = 1.0) -> pd.DataFrame:
        min_var_result = self.optimize_min_variance(min_weight, max_weight)
        max_return = self.mean_returns.max()
        min_return = min_var_result.expected_return
        
        # Fix: handle negative max_return properly
        upper_target = max_return - 0.05 * abs(max_return - min_return) if max_return != min_return else max_return
        target_returns = np.linspace(min_return, upper_target, n_points)
        
        frontier_data = []
        for target in target_returns:
            result = self.optimize_min_variance(min_weight, max_weight, target_return=target)
            if result.status == "optimal":
                frontier_data.append({
                    "expected_return": result.expected_return,
                    "volatility": result.volatility,
                    "sharpe_ratio": result.sharpe_ratio,
                    "cvar_95": result.cvar_95,
                    "cvar_99": result.cvar_99,
                })
        
        return pd.DataFrame(frontier_data)
    
    def get_equal_weight_metrics(self) -> dict:
        weights = np.ones(self.n_assets) / self.n_assets
        return self._compute_portfolio_metrics(weights)


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_return_distribution_chart(portfolio_returns: np.ndarray, var_95: float, 
                                      cvar_95: float, var_99: float) -> go.Figure:
    """Create an interactive histogram of portfolio returns with VaR/CVaR markers."""
    
    fig = go.Figure()
    
    # Histogram
    fig.add_trace(go.Histogram(
        x=portfolio_returns * 100,
        nbinsx=100,
        name="Return Distribution",
        marker_color="#2d5a87",
        opacity=0.7,
        hovertemplate="Return: %{x:.1f}%<br>Count: %{y}<extra></extra>"
    ))
    
    # VaR 95% line
    fig.add_vline(x=var_95 * 100, line_width=2, line_dash="dash", line_color="#ffc107",
                  annotation_text=f"VaR 95%: {var_95:.1%}", annotation_position="top left")
    
    # CVaR 95% line
    fig.add_vline(x=cvar_95 * 100, line_width=2, line_dash="dot", line_color="#fd7e14",
                  annotation_text=f"CVaR 95%: {cvar_95:.1%}", annotation_position="top left")
    
    # VaR 99% line
    fig.add_vline(x=var_99 * 100, line_width=2, line_dash="dash", line_color="#dc3545",
                  annotation_text=f"VaR 99%: {var_99:.1%}", annotation_position="bottom left")
    
    # Mean line
    mean_ret = np.mean(portfolio_returns)
    fig.add_vline(x=mean_ret * 100, line_width=2, line_color="#28a745",
                  annotation_text=f"Mean: {mean_ret:.1%}", annotation_position="top right")
    
    fig.update_layout(
        title=dict(text="Portfolio Return Distribution", font=dict(size=18, color="#1e3a5f")),
        xaxis_title="Return (%)",
        yaxis_title="Frequency",
        template="plotly_white",
        height=400,
        showlegend=False,
        margin=dict(l=50, r=50, t=60, b=50),
    )
    
    return fig


def create_weights_chart(weights: pd.Series) -> go.Figure:
    """Create a donut chart for portfolio weights."""
    
    colors = px.colors.qualitative.Set2[:len(weights)]
    
    fig = go.Figure(data=[go.Pie(
        labels=weights.index,
        values=weights.values * 100,
        hole=0.5,
        marker_colors=colors,
        textinfo="label+percent",
        textposition="outside",
        hovertemplate="%{label}<br>Weight: %{value:.1f}%<extra></extra>"
    )])
    
    fig.update_layout(
        title=dict(text="Portfolio Allocation", font=dict(size=18, color="#1e3a5f")),
        template="plotly_white",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=80),
        annotations=[dict(text="Weights", x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    
    return fig


def create_efficient_frontier_chart(frontier: pd.DataFrame, current_result: OptimizationResult,
                                     benchmark: dict) -> go.Figure:
    """Create efficient frontier with current portfolio and benchmark."""
    
    fig = go.Figure()
    
    # Efficient frontier line
    fig.add_trace(go.Scatter(
        x=frontier["volatility"] * 100,
        y=frontier["expected_return"] * 100,
        mode="lines",
        name="Efficient Frontier",
        line=dict(color="#1e3a5f", width=3),
        hovertemplate="Volatility: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>"
    ))
    
    # Current portfolio
    fig.add_trace(go.Scatter(
        x=[current_result.volatility * 100],
        y=[current_result.expected_return * 100],
        mode="markers",
        name="Optimized Portfolio",
        marker=dict(color="#28a745", size=15, symbol="star"),
        hovertemplate="Volatility: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>"
    ))
    
    # Benchmark (equal weight)
    fig.add_trace(go.Scatter(
        x=[benchmark["volatility"] * 100],
        y=[benchmark["expected_return"] * 100],
        mode="markers",
        name="Equal Weight",
        marker=dict(color="#6c757d", size=12, symbol="circle"),
        hovertemplate="Volatility: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text="Efficient Frontier", font=dict(size=18, color="#1e3a5f")),
        xaxis_title="Volatility (%)",
        yaxis_title="Expected Return (%)",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=50, r=50, t=60, b=80),
    )
    
    return fig


def create_cvar_frontier_chart(frontier: pd.DataFrame, current_result: OptimizationResult) -> go.Figure:
    """Create return vs CVaR chart."""
    
    fig = go.Figure()
    
    # CVaR frontier
    fig.add_trace(go.Scatter(
        x=frontier["cvar_95"].abs() * 100,
        y=frontier["expected_return"] * 100,
        mode="lines+markers",
        name="Return vs CVaR",
        line=dict(color="#fd7e14", width=2),
        marker=dict(size=6),
        hovertemplate="CVaR 95%: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>"
    ))
    
    # Current portfolio
    fig.add_trace(go.Scatter(
        x=[abs(current_result.cvar_95) * 100],
        y=[current_result.expected_return * 100],
        mode="markers",
        name="Optimized Portfolio",
        marker=dict(color="#28a745", size=15, symbol="star"),
    ))
    
    fig.update_layout(
        title=dict(text="Return vs Tail Risk (CVaR 95%)", font=dict(size=18, color="#1e3a5f")),
        xaxis_title="CVaR 95% Loss (%)",
        yaxis_title="Expected Return (%)",
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=50, r=50, t=60, b=80),
    )
    
    return fig


def create_scenario_heatmap(returns_df: pd.DataFrame, weights: pd.Series) -> go.Figure:
    """Create heatmap of weighted returns by asset."""
    
    # Calculate weighted returns for a sample of scenarios
    sample_size = min(100, len(returns_df))
    sample_idx = np.linspace(0, len(returns_df)-1, sample_size, dtype=int)
    
    weighted_returns = returns_df.iloc[sample_idx] * weights
    
    fig = go.Figure(data=go.Heatmap(
        z=weighted_returns.values.T * 100,
        x=[f"S{i}" for i in sample_idx],
        y=weighted_returns.columns,
        colorscale="RdYlGn",
        zmid=0,
        colorbar=dict(title="Return (%)"),
        hovertemplate="Scenario: %{x}<br>Asset: %{y}<br>Contribution: %{z:.2f}%<extra></extra>"
    ))
    
    fig.update_layout(
        title=dict(text="Weighted Return Contribution (Sample Scenarios)", font=dict(size=18, color="#1e3a5f")),
        xaxis_title="Scenario",
        yaxis_title="Asset",
        template="plotly_white",
        height=300,
        margin=dict(l=50, r=50, t=60, b=50),
    )
    
    return fig


def create_probability_chart(portfolio_returns: np.ndarray) -> go.Figure:
    """Create cumulative probability distribution chart."""
    
    sorted_returns = np.sort(portfolio_returns)
    cumulative_prob = np.arange(1, len(sorted_returns) + 1) / len(sorted_returns)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=sorted_returns * 100,
        y=cumulative_prob * 100,
        mode="lines",
        name="CDF",
        line=dict(color="#1e3a5f", width=2),
        fill="tozeroy",
        fillcolor="rgba(45, 90, 135, 0.1)",
        hovertemplate="Return: %{x:.1f}%<br>P(R ≤ x): %{y:.1f}%<extra></extra>"
    ))
    
    # Add key probability markers
    for prob, label in [(1, "1%"), (5, "5%"), (50, "50%"), (95, "95%")]:
        ret = np.percentile(portfolio_returns, prob) * 100
        fig.add_trace(go.Scatter(
            x=[ret], y=[prob],
            mode="markers+text",
            name=f"P{prob}",
            marker=dict(size=10, color="#fd7e14"),
            text=[f"{label}: {ret:.1f}%"],
            textposition="top center",
            showlegend=False
        ))
    
    fig.update_layout(
        title=dict(text="Cumulative Return Distribution", font=dict(size=18, color="#1e3a5f")),
        xaxis_title="Return (%)",
        yaxis_title="Cumulative Probability (%)",
        template="plotly_white",
        height=400,
        showlegend=False,
        margin=dict(l=50, r=50, t=60, b=50),
    )
    
    return fig


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    """Load scenario returns data."""
    return pd.read_csv(file_path, index_col=0)


def compute_additional_stats(portfolio_returns: np.ndarray, rf: float = 0.04) -> dict:
    """Compute additional portfolio statistics."""
    
    returns = portfolio_returns
    
    # Probability metrics
    prob_positive = (returns > 0).mean()
    prob_loss_5 = (returns < -0.05).mean()
    prob_loss_10 = (returns < -0.10).mean()
    prob_loss_25 = (returns < -0.25).mean()
    prob_loss_50 = (returns < -0.50).mean()
    
    # Percentiles
    p1 = np.percentile(returns, 1)
    p5 = np.percentile(returns, 5)
    p10 = np.percentile(returns, 10)
    p25 = np.percentile(returns, 25)
    p50 = np.percentile(returns, 50)
    p75 = np.percentile(returns, 75)
    p90 = np.percentile(returns, 90)
    p95 = np.percentile(returns, 95)
    p99 = np.percentile(returns, 99)
    
    # Moments
    skewness = pd.Series(returns).skew()
    kurtosis = pd.Series(returns).kurtosis()
    
    # Standard downside deviation (Sortino): sqrt(mean(min(r - MAR, 0)^2))
    downside_diff = np.minimum(returns - rf, 0)
    downside_dev = np.sqrt(np.mean(downside_diff ** 2))
    
    # Sortino ratio
    excess_return = np.mean(returns) - rf
    sortino = excess_return / downside_dev if downside_dev > 0 else 0
    
    return {
        "prob_positive": prob_positive,
        "prob_loss_5": prob_loss_5,
        "prob_loss_10": prob_loss_10,
        "prob_loss_25": prob_loss_25,
        "prob_loss_50": prob_loss_50,
        "p1": p1, "p5": p5, "p10": p10, "p25": p25, "p50": p50,
        "p75": p75, "p90": p90, "p95": p95, "p99": p99,
        "skewness": skewness,
        "kurtosis": kurtosis,
        "downside_dev": downside_dev,
        "sortino_ratio": sortino,
    }


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌪️ Cat Bond Portfolio Optimizer</h1>
        <p>Advanced portfolio optimization with scenario-based risk analytics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data - with file upload option
    data_path = Path(__file__).parent / "data" / "scenario_returns.csv"
    
    with st.sidebar:
        st.markdown("### \U0001F4C1 Data Source")
        
        uploaded_file = st.file_uploader(
            "Upload custom returns data",
            type=["csv", "xlsx", "xls"],
            help="Upload a CSV or Excel file with scenario returns. First column = scenario index, other columns = asset returns."
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.lower().endswith('.csv'):
                    returns_df = pd.read_csv(uploaded_file, index_col=0)
                else:
                    returns_df = pd.read_excel(uploaded_file, index_col=0)
                
                # Validate
                returns_df = returns_df.apply(pd.to_numeric, errors='coerce')
                returns_df = returns_df.dropna(axis=1, how='all').dropna(axis=0, how='all')
                
                if returns_df.shape[1] < 2:
                    st.error("Need at least 2 assets")
                    return
                if returns_df.shape[0] < 10:
                    st.error("Need at least 10 scenarios")
                    return
                
                st.success(f"\u2705 Loaded {returns_df.shape[0]:,} scenarios \u00d7 {returns_df.shape[1]} assets")
            except Exception as e:
                st.error(f"Error reading file: {e}")
                return
        elif data_path.exists():
            returns_df = load_data(str(data_path))
        else:
            st.error(f"Data file not found: {data_path}")
            st.info("Please run `generate_sample_data.py` first or upload your own data.")
            return
    
    # Sidebar - Optimization Settings
    with st.sidebar:
        st.markdown("### ⚙️ Optimization Settings")
        
        # Risk-free rate
        rf_rate = st.number_input(
            "Risk-Free Rate (%)",
            min_value=0.0, max_value=20.0, value=4.0, step=0.1,
            help="Annual risk-free rate for Sharpe ratio calculation"
        ) / 100
        
        st.markdown("---")
        st.markdown("### 🎯 Optimization Objective")
        
        opt_method = st.selectbox(
            "Method",
            options=[
                "Maximum Sharpe Ratio",
                "Minimum Variance",
                "Minimum CVaR",
                "Mean-CVaR Trade-off",
                "Maximum Return (Constrained)",
                "Exponential Utility (CARA)",
            ],
            help="Select the optimization objective"
        )
        
        # Method descriptions
        method_descriptions = {
            "Maximum Sharpe Ratio": {
                "goal": "Find the portfolio with the highest risk-adjusted return.",
                "description": "Maximizes the ratio of excess return (above risk-free rate) to volatility. The tangency portfolio on the efficient frontier.",
                "formula": r"SR = \frac{E[R_p] - R_f}{\sigma_p}",
                "best_for": "Investors seeking the most efficient risk-return trade-off."
            },
            "Minimum Variance": {
                "goal": "Find the portfolio with the lowest possible volatility.",
                "description": "Minimizes portfolio standard deviation through diversification. Often allocates to low-correlation assets.",
                "formula": r"\min \sqrt{w^T \Sigma w}",
                "best_for": "Conservative investors prioritizing stability over returns."
            },
            "Minimum CVaR": {
                "goal": "Minimize expected losses in worst-case scenarios.",
                "description": "Minimizes Conditional Value at Risk (Expected Shortfall) \u2014 the average loss in the worst \u03b1% of scenarios. Uses the Rockafellar-Uryasev LP formulation.",
                "formula": r"\min CVaR_\alpha = E[L \mid L > VaR_\alpha]",
                "best_for": "Risk-averse investors focused on tail risk protection."
            },
            "Mean-CVaR Trade-off": {
                "goal": "Balance expected return against tail risk.",
                "description": "Optimizes a weighted combination of return and CVaR: min(-E[R] + \u03bb\u00b7CVaR). The risk aversion parameter \u03bb controls the trade-off.",
                "formula": r"\min \; -E[R] + \lambda \cdot CVaR_\alpha",
                "best_for": "Investors who want explicit control over risk-return preferences."
            },
            "Maximum Return (Constrained)": {
                "goal": "Maximize expected return within a risk budget.",
                "description": "Finds the highest-return portfolio subject to a volatility or CVaR constraint. Useful when risk limits are externally imposed.",
                "formula": r"\max E[R] \;\; \text{s.t.} \;\; \sigma \leq \sigma_{max}",
                "best_for": "Portfolio managers with regulatory or mandate-driven risk limits."
            },
            "Exponential Utility (CARA)": {
                "goal": "Optimize using a theoretically grounded risk-aversion model.",
                "description": "Maximizes expected exponential (CARA) utility: U(W) = -e^(-C\u00b7W). Higher C penalizes downside more heavily. Based on Elton/Gruber's Modern Portfolio Theory.",
                "formula": r"\max E[U] = E[-e^{-C \cdot 50 \cdot R}]",
                "best_for": "Quantitative investors with well-defined risk preferences."
            }
        }
        
        with st.expander("\U0001F4D6 About this method"):
            info = method_descriptions.get(opt_method, {})
            st.markdown(f"**Goal:** {info.get('goal', '')}")
            st.markdown(info.get('description', ''))
            if info.get('formula'):
                st.latex(info['formula'])
            st.markdown(f"*Best for: {info.get('best_for', '')}*")
        
        # Method-specific parameters
        if opt_method == "Minimum CVaR":
            cvar_alpha = st.slider(
                "CVaR Confidence Level (%)",
                min_value=90, max_value=99, value=95,
                help="Confidence level for CVaR (e.g., 95% = worst 5% of scenarios)"
            )
        elif opt_method == "Mean-CVaR Trade-off":
            risk_aversion = st.slider(
                "Risk Aversion (λ)",
                min_value=0.1, max_value=5.0, value=1.0, step=0.1,
                help="Higher values = more risk averse (more weight on CVaR reduction)"
            )
            cvar_alpha = st.slider(
                "CVaR Confidence Level (%)",
                min_value=90, max_value=99, value=95
            )
        elif opt_method == "Maximum Return (Constrained)":
            constraint_type = st.radio(
                "Constraint Type",
                options=["Volatility", "CVaR"],
                horizontal=True
            )
            if constraint_type == "Volatility":
                max_vol = st.slider(
                    "Maximum Volatility (%)",
                    min_value=5.0, max_value=30.0, value=10.0, step=0.5
                ) / 100
            else:
                max_cvar_val = st.slider(
                    "Maximum CVaR Loss (%)",
                    min_value=10.0, max_value=50.0, value=25.0, step=1.0
                ) / 100
        elif opt_method == "Exponential Utility (CARA)":
            st.markdown(r"""
            **Elton/Gruber Utility Function:**
            
            Based on Chapter 10 of *Modern Portfolio Theory*.
            
            $U(W) = -e^{-C \cdot W}$
            
            $V = -\frac{e^{-C \cdot 50 \cdot r}}{C}$
            """)
            exp_risk_aversion = st.slider(
                "Risk Aversion (C)",
                min_value=0.01, max_value=1.0, value=0.5, step=0.01,
                help="C ≈ 0: Risk-neutral (maximize return)\nC = 1: Highly risk-averse"
            )
        
        st.markdown("---")
        st.markdown("### 📊 Weight Constraints")
        
        col1, col2 = st.columns(2)
        with col1:
            min_weight = st.number_input(
                "Min Weight (%)",
                min_value=0.0, max_value=50.0, value=0.0, step=1.0
            ) / 100
        with col2:
            max_weight = st.number_input(
                "Max Weight (%)",
                min_value=10.0, max_value=100.0, value=100.0, step=1.0
            ) / 100
        
        st.markdown("---")
        
        # Run optimization button
        run_opt = st.button("🚀 Run Optimization", use_container_width=True)
    
    # Initialize optimizer
    optimizer = CatBondOptimizer(returns_df, risk_free_rate=rf_rate)
    
    # Run optimization based on selected method
    if run_opt or "result" not in st.session_state:
        if opt_method == "Maximum Sharpe Ratio":
            result = optimizer.optimize_max_sharpe(min_weight, max_weight)
        elif opt_method == "Minimum Variance":
            result = optimizer.optimize_min_variance(min_weight, max_weight)
        elif opt_method == "Minimum CVaR":
            alpha = (100 - cvar_alpha) / 100
            result = optimizer.optimize_min_cvar(alpha, min_weight, max_weight)
        elif opt_method == "Mean-CVaR Trade-off":
            alpha = (100 - cvar_alpha) / 100
            result = optimizer.optimize_mean_cvar(alpha, risk_aversion, min_weight, max_weight)
        elif opt_method == "Maximum Return (Constrained)":
            if constraint_type == "Volatility":
                result = optimizer.optimize_max_return(max_volatility=max_vol, 
                                                        min_weight=min_weight, max_weight=max_weight)
            else:
                result = optimizer.optimize_max_return(max_cvar=max_cvar_val,
                                                        min_weight=min_weight, max_weight=max_weight)
        else:  # Exponential Utility (CARA)
            result = optimizer.optimize_exponential_utility(
                risk_aversion=exp_risk_aversion,
                min_weight=min_weight, max_weight=max_weight
            )
        
        st.session_state.result = result
    
    result = st.session_state.result
    benchmark = optimizer.get_equal_weight_metrics()
    additional_stats = compute_additional_stats(result.portfolio_returns, rf=rf_rate)
    
    # Status indicator
    if result.status == "optimal":
        st.success(f"✅ Optimization completed successfully | Method: **{opt_method}**")
    else:
        st.warning(f"⚠️ {result.status}")
    
    # Main metrics row
    st.markdown('<p class="section-header">📈 Key Performance Metrics</p>', unsafe_allow_html=True)
    
    metric_cols = st.columns(6)
    
    metrics_data = [
        ("Expected Return", f"{result.expected_return:.2%}", "positive" if result.expected_return > 0 else "negative"),
        ("Volatility", f"{result.volatility:.2%}", "neutral"),
        ("Sharpe Ratio", f"{result.sharpe_ratio:.2f}", "positive" if result.sharpe_ratio > 0 else "negative"),
        ("VaR 95%", f"{result.var_95:.2%}", "negative"),
        ("CVaR 95%", f"{result.cvar_95:.2%}", "negative"),
        ("Worst Scenario", f"{result.worst_scenario:.2%}", "negative"),
    ]
    
    for col, (label, value, color) in zip(metric_cols, metrics_data):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-value metric-{color}">{value}</p>
                <p class="metric-label">{label}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts section
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Distribution", "🎯 Allocation", "📈 Frontiers", "📋 Statistics"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            dist_chart = create_return_distribution_chart(
                result.portfolio_returns, result.var_95, result.cvar_95, result.var_99
            )
            st.plotly_chart(dist_chart, use_container_width=True)
        
        with col2:
            prob_chart = create_probability_chart(result.portfolio_returns)
            st.plotly_chart(prob_chart, use_container_width=True)
        
        # Scenario heatmap
        heatmap = create_scenario_heatmap(returns_df, result.weights)
        st.plotly_chart(heatmap, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            weights_chart = create_weights_chart(result.weights)
            st.plotly_chart(weights_chart, use_container_width=True)
        
        with col2:
            st.markdown('<p class="section-header">Portfolio Weights</p>', unsafe_allow_html=True)
            
            weights_df = pd.DataFrame({
                "Asset": result.weights.index,
                "Weight (%)": (result.weights.values * 100).round(2),
                "Exp. Return (%)": (returns_df.mean() * 100).round(2),
                "Volatility (%)": (returns_df.std() * 100).round(2),
            })
            weights_df = weights_df.set_index("Asset")
            
            st.dataframe(
                weights_df.style.format({
                    "Weight (%)": "{:.2f}%",
                    "Exp. Return (%)": "{:.2f}%",
                    "Volatility (%)": "{:.2f}%"
                }).background_gradient(subset=["Weight (%)"], cmap="Blues"),
                use_container_width=True,
                height=250
            )
            
            # Comparison with benchmark
            st.markdown('<p class="section-header">vs Equal Weight Benchmark</p>', unsafe_allow_html=True)
            
            comp_data = {
                "Metric": ["Expected Return", "Volatility", "Sharpe Ratio", "CVaR 95%"],
                "Optimized": [
                    f"{result.expected_return:.2%}",
                    f"{result.volatility:.2%}",
                    f"{result.sharpe_ratio:.2f}",
                    f"{result.cvar_95:.2%}"
                ],
                "Equal Weight": [
                    f"{benchmark['expected_return']:.2%}",
                    f"{benchmark['volatility']:.2%}",
                    f"{benchmark['sharpe_ratio']:.2f}",
                    f"{benchmark['cvar_95']:.2%}"
                ],
            }
            st.dataframe(pd.DataFrame(comp_data).set_index("Metric"), use_container_width=True)
    
    with tab3:
        # Compute efficient frontier
        with st.spinner("Computing efficient frontier..."):
            frontier = optimizer.efficient_frontier(n_points=25, min_weight=min_weight, max_weight=max_weight)
        
        col1, col2 = st.columns(2)
        
        with col1:
            ef_chart = create_efficient_frontier_chart(frontier, result, benchmark)
            st.plotly_chart(ef_chart, use_container_width=True)
        
        with col2:
            cvar_chart = create_cvar_frontier_chart(frontier, result)
            st.plotly_chart(cvar_chart, use_container_width=True)
    
    with tab4:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<p class="section-header">🎲 Probability Metrics</p>', unsafe_allow_html=True)
            prob_data = {
                "Metric": [
                    "P(Return > 0)",
                    "P(Loss > 5%)",
                    "P(Loss > 10%)",
                    "P(Loss > 25%)",
                    "P(Loss > 50%)",
                ],
                "Value": [
                    f"{additional_stats['prob_positive']:.1%}",
                    f"{additional_stats['prob_loss_5']:.1%}",
                    f"{additional_stats['prob_loss_10']:.1%}",
                    f"{additional_stats['prob_loss_25']:.1%}",
                    f"{additional_stats['prob_loss_50']:.1%}",
                ]
            }
            st.dataframe(pd.DataFrame(prob_data).set_index("Metric"), use_container_width=True)
        
        with col2:
            st.markdown('<p class="section-header">📊 Percentiles</p>', unsafe_allow_html=True)
            pct_data = {
                "Percentile": ["1st", "5th", "10th", "25th", "50th (Median)", "75th", "90th", "95th", "99th"],
                "Return": [
                    f"{additional_stats['p1']:.2%}",
                    f"{additional_stats['p5']:.2%}",
                    f"{additional_stats['p10']:.2%}",
                    f"{additional_stats['p25']:.2%}",
                    f"{additional_stats['p50']:.2%}",
                    f"{additional_stats['p75']:.2%}",
                    f"{additional_stats['p90']:.2%}",
                    f"{additional_stats['p95']:.2%}",
                    f"{additional_stats['p99']:.2%}",
                ]
            }
            st.dataframe(pd.DataFrame(pct_data).set_index("Percentile"), use_container_width=True)
        
        with col3:
            st.markdown('<p class="section-header">📐 Risk Metrics</p>', unsafe_allow_html=True)
            risk_data = {
                "Metric": [
                    "VaR 95%",
                    "VaR 99%",
                    "CVaR 95% (ES)",
                    "CVaR 99% (ES)",
                    "Downside Deviation",
                    "Sortino Ratio",
                    "Skewness",
                    "Excess Kurtosis",
                ],
                "Value": [
                    f"{result.var_95:.2%}",
                    f"{result.var_99:.2%}",
                    f"{result.cvar_95:.2%}",
                    f"{result.cvar_99:.2%}",
                    f"{additional_stats['downside_dev']:.2%}",
                    f"{additional_stats['sortino_ratio']:.2f}",
                    f"{additional_stats['skewness']:.2f}",
                    f"{additional_stats['kurtosis']:.2f}",
                ]
            }
            st.dataframe(pd.DataFrame(risk_data).set_index("Metric"), use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #6c757d; font-size: 0.85rem;'>"
        f"📊 Analyzing {len(returns_df):,} scenarios across {len(returns_df.columns)} assets | "
        "Cat Bond Portfolio Optimizer v1.0"
        "</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
