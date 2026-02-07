"""Tests for compute_additional_stats helper."""

from __future__ import annotations

import numpy as np

from app.services.stats import compute_additional_stats


class TestComputeAdditionalStats:
    """Tests for Portfolio stats computation."""

    def test_compute_additional_stats_returns_expected_keys(self) -> None:
        rng = np.random.default_rng(42)
        returns = rng.normal(0.04, 0.05, size=500)
        stats = compute_additional_stats(returns, rf=0.04)
        expected_keys = {
            "prob_positive", "prob_loss_5", "prob_loss_10",
            "prob_loss_25", "prob_loss_50",
            "p1", "p5", "p10", "p25", "p50", "p75", "p90", "p95", "p99",
            "skewness", "kurtosis", "downside_dev", "sortino_ratio",
        }
        assert expected_keys.issubset(set(stats.keys()))

    def test_sortino_ratio_calculation(self) -> None:
        """Sortino ratio should be positive for returns above rf."""
        rng = np.random.default_rng(42)
        returns = rng.normal(0.08, 0.02, size=1000)
        stats = compute_additional_stats(returns, rf=0.04)
        assert stats["sortino_ratio"] > 0.0

    def test_sortino_ratio_negative_for_low_returns(self) -> None:
        """Sortino ratio should be negative when mean < rf."""
        rng = np.random.default_rng(42)
        returns = rng.normal(-0.05, 0.02, size=1000)
        stats = compute_additional_stats(returns, rf=0.04)
        assert stats["sortino_ratio"] < 0.0

    def test_probability_values_in_range(self) -> None:
        rng = np.random.default_rng(42)
        returns = rng.normal(0.04, 0.10, size=500)
        stats = compute_additional_stats(returns, rf=0.04)
        for key in ("prob_positive", "prob_loss_5", "prob_loss_10"):
            assert 0.0 <= stats[key] <= 1.0

    def test_percentiles_are_monotonic(self) -> None:
        rng = np.random.default_rng(42)
        returns = rng.normal(0.04, 0.10, size=500)
        stats = compute_additional_stats(returns, rf=0.04)
        pcts = [stats[f"p{p}"] for p in (1, 5, 10, 25, 50, 75, 90, 95, 99)]
        for i in range(len(pcts) - 1):
            assert pcts[i] <= pcts[i + 1] + 1e-10
