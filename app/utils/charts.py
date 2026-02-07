"""Plotly chart-building utilities for the portfolio optimizer web UI.

Each function returns a ``plotly.graph_objects.Figure`` ready to be
serialised with ``fig.to_json()`` and rendered client-side via Plotly.js.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_return_distribution_chart(
    portfolio_returns: np.ndarray,
    var_95: float,
    cvar_95: float,
    var_99: float,
) -> go.Figure:
    """Create a histogram of portfolio return distribution with risk markers.

    Args:
        portfolio_returns: 1-D array of simulated portfolio returns.
        var_95: Value-at-Risk at 95 % confidence (5th percentile).
        cvar_95: Conditional VaR at 95 % confidence.
        var_99: Value-at-Risk at 99 % confidence (1st percentile).

    Returns:
        Plotly Figure with histogram and vertical risk/mean lines.
    """
    returns_pct = portfolio_returns * 100
    mean_return = float(np.mean(returns_pct))

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=returns_pct,
            nbinsx=100,
            marker_color="#2d5a87",
            opacity=0.7,
            name="Return Distribution",
        )
    )

    # VaR 95 % — dashed yellow
    fig.add_vline(
        x=var_95 * 100,
        line_dash="dash",
        line_color="#ffc107",
        annotation_text=f"VaR 95%: {var_95 * 100:.2f}%",
        annotation_position="top left",
    )

    # CVaR 95 % — dotted orange
    fig.add_vline(
        x=cvar_95 * 100,
        line_dash="dot",
        line_color="#fd7e14",
        annotation_text=f"CVaR 95%: {cvar_95 * 100:.2f}%",
        annotation_position="top left",
    )

    # VaR 99 % — dashed red
    fig.add_vline(
        x=var_99 * 100,
        line_dash="dash",
        line_color="#dc3545",
        annotation_text=f"VaR 99%: {var_99 * 100:.2f}%",
        annotation_position="top left",
    )

    # Mean — solid green
    fig.add_vline(
        x=mean_return,
        line_dash="solid",
        line_color="#28a745",
        annotation_text=f"Mean: {mean_return:.2f}%",
        annotation_position="top right",
    )

    fig.update_layout(
        title="Portfolio Return Distribution",
        xaxis_title="Return (%)",
        yaxis_title="Frequency",
        template="plotly_white",
        height=400,
        showlegend=False,
    )

    return fig


def create_weights_chart(weights: Dict[str, float]) -> go.Figure:
    """Create a donut chart of portfolio allocation weights.

    Args:
        weights: Mapping of asset name to weight (0–1).

    Returns:
        Plotly Figure with a donut (pie with hole) chart.
    """
    names = list(weights.keys())
    values = list(weights.values())
    colors = px.colors.qualitative.Set2

    fig = go.Figure(
        go.Pie(
            labels=names,
            values=values,
            hole=0.5,
            marker=dict(colors=colors[: len(names)]),
            textinfo="label+percent",
            textposition="outside",
        )
    )

    fig.update_layout(
        title="Portfolio Weights",
        annotations=[
            dict(text="Weights", x=0.5, y=0.5, font_size=16, showarrow=False)
        ],
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        height=400,
    )

    return fig


def create_efficient_frontier_chart(
    frontier_data: List[Dict[str, float]],
    current_metrics: Dict[str, float],
    benchmark_metrics: Dict[str, float],
) -> go.Figure:
    """Create an efficient frontier chart with portfolio and benchmark markers.

    Args:
        frontier_data: List of dicts each containing ``expected_return``,
            ``volatility``, ``sharpe_ratio``, and ``cvar_95``.
        current_metrics: Dict with ``expected_return`` and ``volatility``
            for the optimised portfolio.
        benchmark_metrics: Dict with ``expected_return`` and ``volatility``
            for the equal-weight benchmark.

    Returns:
        Plotly Figure with frontier line and marker overlays.
    """
    vol = [d["volatility"] * 100 for d in frontier_data]
    ret = [d["expected_return"] * 100 for d in frontier_data]

    fig = go.Figure()

    # Frontier line
    fig.add_trace(
        go.Scatter(
            x=vol,
            y=ret,
            mode="lines",
            name="Efficient Frontier",
            line=dict(color="#1e3a5f", width=3),
        )
    )

    # Current portfolio
    fig.add_trace(
        go.Scatter(
            x=[current_metrics["volatility"] * 100],
            y=[current_metrics["expected_return"] * 100],
            mode="markers",
            name="Current Portfolio",
            marker=dict(color="#28a745", size=15, symbol="star"),
        )
    )

    # Benchmark
    fig.add_trace(
        go.Scatter(
            x=[benchmark_metrics["volatility"] * 100],
            y=[benchmark_metrics["expected_return"] * 100],
            mode="markers",
            name="Benchmark (Equal Weight)",
            marker=dict(color="#6c757d", size=12, symbol="circle"),
        )
    )

    fig.update_layout(
        title="Efficient Frontier",
        xaxis_title="Volatility (%)",
        yaxis_title="Expected Return (%)",
        template="plotly_white",
        height=400,
    )

    return fig


def create_cvar_frontier_chart(
    frontier_data: List[Dict[str, float]],
    current_metrics: Dict[str, float],
) -> go.Figure:
    """Create a CVaR-return frontier chart.

    Args:
        frontier_data: List of dicts each containing ``expected_return``
            and ``cvar_95``.
        current_metrics: Dict with ``expected_return`` and ``cvar_95``
            for the optimised portfolio.

    Returns:
        Plotly Figure with the CVaR frontier and a current-portfolio marker.
    """
    cvar_vals = [abs(d["cvar_95"]) * 100 for d in frontier_data]
    ret_vals = [d["expected_return"] * 100 for d in frontier_data]

    fig = go.Figure()

    # CVaR frontier
    fig.add_trace(
        go.Scatter(
            x=cvar_vals,
            y=ret_vals,
            mode="lines+markers",
            name="CVaR Frontier",
            line=dict(color="#fd7e14", width=2),
            marker=dict(color="#fd7e14", size=6),
        )
    )

    # Current portfolio
    fig.add_trace(
        go.Scatter(
            x=[abs(current_metrics["cvar_95"]) * 100],
            y=[current_metrics["expected_return"] * 100],
            mode="markers",
            name="Current Portfolio",
            marker=dict(color="#28a745", size=15, symbol="star"),
        )
    )

    fig.update_layout(
        title="CVaR Frontier",
        xaxis_title="|CVaR 95%| (%)",
        yaxis_title="Expected Return (%)",
        template="plotly_white",
        height=400,
    )

    return fig


def create_scenario_heatmap(
    returns_df: pd.DataFrame,
    weights_dict: Dict[str, float],
) -> go.Figure:
    """Create a heatmap of weighted scenario returns.

    Samples 100 evenly-spaced scenarios, computes weighted returns per
    asset, and displays them as a colour-mapped grid.

    Args:
        returns_df: DataFrame of shape (n_scenarios, n_assets).
        weights_dict: Mapping of asset name to portfolio weight.

    Returns:
        Plotly Figure with an ``RdYlGn`` heatmap centred on zero.
    """
    n_scenarios = len(returns_df)
    indices = np.linspace(0, n_scenarios - 1, min(100, n_scenarios), dtype=int)
    sampled = returns_df.iloc[indices]

    weights_series = pd.Series(weights_dict)
    # Align to columns present in returns_df
    weights_series = weights_series.reindex(returns_df.columns, fill_value=0.0)

    weighted_returns = sampled * weights_series

    fig = go.Figure(
        go.Heatmap(
            z=weighted_returns.T.values * 100,
            x=[str(i) for i in indices],
            y=list(returns_df.columns),
            colorscale="RdYlGn",
            zmid=0,
            colorbar=dict(title="Return (%)"),
        )
    )

    fig.update_layout(
        title="Scenario Heatmap (Weighted Returns %)",
        xaxis_title="Scenario",
        yaxis_title="Asset",
        height=300,
    )

    return fig


def create_probability_chart(portfolio_returns: np.ndarray) -> go.Figure:
    """Create a cumulative distribution function (CDF) chart.

    Args:
        portfolio_returns: 1-D array of simulated portfolio returns.

    Returns:
        Plotly Figure with CDF line, fill, and key-percentile markers.
    """
    sorted_returns = np.sort(portfolio_returns) * 100
    n = len(sorted_returns)
    cum_prob = np.arange(1, n + 1) / n

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=sorted_returns,
            y=cum_prob,
            mode="lines",
            name="CDF",
            line=dict(color="#2d5a87", width=2),
            fill="tozeroy",
            fillcolor="rgba(45, 90, 135, 0.15)",
        )
    )

    # Key probability markers at 1 %, 5 %, 50 %, 95 %
    percentiles = [1, 5, 50, 95]
    for p in percentiles:
        idx = max(0, int(n * p / 100) - 1)
        fig.add_trace(
            go.Scatter(
                x=[sorted_returns[idx]],
                y=[cum_prob[idx]],
                mode="markers+text",
                name=f"{p}th percentile",
                marker=dict(color="#fd7e14", size=10),
                text=[f"{p}%: {sorted_returns[idx]:.2f}%"],
                textposition="top right",
                showlegend=False,
            )
        )

    fig.update_layout(
        title="Cumulative Probability Distribution",
        xaxis_title="Return (%)",
        yaxis_title="Cumulative Probability",
        template="plotly_white",
        height=400,
    )

    return fig
