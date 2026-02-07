"""Tests for Plotly chart-building utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app.utils.charts import (
    create_cvar_frontier_chart,
    create_efficient_frontier_chart,
    create_probability_chart,
    create_return_distribution_chart,
    create_scenario_heatmap,
    create_weights_chart,
)


def _sample_returns(n: int = 500) -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.normal(0.04, 0.10, size=n)


def _sample_frontier() -> list[dict[str, float]]:
    return [
        {"expected_return": 0.03, "volatility": 0.05, "sharpe_ratio": 0.4, "cvar_95": -0.10},
        {"expected_return": 0.05, "volatility": 0.08, "sharpe_ratio": 0.5, "cvar_95": -0.15},
        {"expected_return": 0.07, "volatility": 0.12, "sharpe_ratio": 0.45, "cvar_95": -0.20},
    ]


class TestDistributionChart:
    def test_distribution_chart_returns_figure(self) -> None:
        fig = create_return_distribution_chart(
            _sample_returns(), var_95=-0.12, cvar_95=-0.18, var_99=-0.25
        )
        assert isinstance(fig, go.Figure)


class TestWeightsChart:
    def test_weights_chart_returns_figure(self) -> None:
        weights = {"Bond_A": 0.4, "Bond_B": 0.35, "Bond_C": 0.25}
        fig = create_weights_chart(weights)
        assert isinstance(fig, go.Figure)


class TestFrontierChart:
    def test_frontier_chart_returns_figure(self) -> None:
        fig = create_efficient_frontier_chart(
            _sample_frontier(),
            {"expected_return": 0.05, "volatility": 0.08},
            {"expected_return": 0.04, "volatility": 0.07},
        )
        assert isinstance(fig, go.Figure)


class TestCvarFrontierChart:
    def test_cvar_frontier_chart_returns_figure(self) -> None:
        fig = create_cvar_frontier_chart(
            _sample_frontier(),
            {"expected_return": 0.05, "cvar_95": -0.15},
        )
        assert isinstance(fig, go.Figure)


class TestHeatmap:
    def test_heatmap_returns_figure(self) -> None:
        rng = np.random.default_rng(42)
        df = pd.DataFrame(
            rng.normal(0.04, 0.05, size=(200, 3)),
            columns=["A", "B", "C"],
        )
        weights_dict = {"A": 0.5, "B": 0.3, "C": 0.2}
        fig = create_scenario_heatmap(df, weights_dict)
        assert isinstance(fig, go.Figure)


class TestProbabilityChart:
    def test_probability_chart_returns_figure(self) -> None:
        fig = create_probability_chart(_sample_returns())
        assert isinstance(fig, go.Figure)
