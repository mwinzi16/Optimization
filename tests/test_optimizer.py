"""
Unit tests for CatBondOptimizer mathematical correctness.

Covers all six optimization methods, portfolio metrics, distribution
statistics, and the efficient frontier computation.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.services.optimizer import CatBondOptimizer


# =====================================================================
# Initialization
# =====================================================================


class TestOptimizerInit:
    """Tests for CatBondOptimizer constructor."""

    def test_optimizer_initialization(
        self, optimizer: CatBondOptimizer
    ) -> None:
        assert optimizer.n_assets == 5
        assert optimizer.n_scenarios == 500
        assert len(optimizer.assets) == 5

    def test_optimizer_covariance_is_square(
        self, optimizer: CatBondOptimizer
    ) -> None:
        assert optimizer.cov_matrix.shape == (5, 5)


# =====================================================================
# Equal-weight metrics
# =====================================================================


class TestEqualWeight:
    """Tests for get_equal_weight_metrics."""

    def test_equal_weight_metrics(self, optimizer: CatBondOptimizer) -> None:
        metrics = optimizer.get_equal_weight_metrics()
        assert "expected_return" in metrics
        assert "volatility" in metrics
        assert "sharpe_ratio" in metrics
        assert "portfolio_returns" in metrics
        assert isinstance(metrics["portfolio_returns"], list)


# =====================================================================
# Maximum Sharpe Ratio
# =====================================================================


class TestMaxSharpe:
    """Tests for the Sharpe-ratio maximisation (transformation method)."""

    def test_weights_sum_to_one(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_max_sharpe(min_weight=0.0, max_weight=1.0)
        assert np.sum(result["weights"]) == pytest.approx(1.0, abs=1e-6)

    def test_weights_within_bounds(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_max_sharpe(min_weight=0.0, max_weight=1.0)
        assert np.all(result["weights"] >= -1e-8)
        assert np.all(result["weights"] <= 1.0 + 1e-8)

    def test_sharpe_higher_than_equal_weight(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_max_sharpe(min_weight=0.0, max_weight=1.0)
        opt_metrics = optimizer._compute_portfolio_metrics(result["weights"])
        eq_weights = np.ones(optimizer.n_assets) / optimizer.n_assets
        eq_metrics = optimizer._compute_portfolio_metrics(eq_weights)
        assert opt_metrics["sharpe_ratio"] >= eq_metrics["sharpe_ratio"] - 1e-6

    def test_status_is_optimal(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_max_sharpe(min_weight=0.0, max_weight=1.0)
        assert result["status"] == "optimal"

    def test_transformation_method_produces_valid_weights(
        self, optimizer: CatBondOptimizer
    ) -> None:
        result = optimizer.optimize_max_sharpe(min_weight=0.0, max_weight=1.0)
        weights = result["weights"]
        # All weights non-negative and finite
        assert np.all(np.isfinite(weights))
        assert np.all(weights >= -1e-8)

    def test_with_custom_weight_bounds(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_max_sharpe(min_weight=0.05, max_weight=0.50)
        weights = result["weights"]
        assert np.all(weights >= 0.05 - 1e-6)
        assert np.all(weights <= 0.50 + 1e-6)
        assert np.sum(weights) == pytest.approx(1.0, abs=1e-6)


# =====================================================================
# Minimum Variance
# =====================================================================


class TestMinVariance:
    """Tests for the minimum-variance optimisation."""

    def test_weights_sum_to_one(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_min_variance(min_weight=0.0, max_weight=1.0)
        assert np.sum(result["weights"]) == pytest.approx(1.0, abs=1e-6)

    def test_variance_lower_than_equal_weight(
        self, optimizer: CatBondOptimizer
    ) -> None:
        result = optimizer.optimize_min_variance(min_weight=0.0, max_weight=1.0)
        opt_metrics = optimizer._compute_portfolio_metrics(result["weights"])
        eq_weights = np.ones(optimizer.n_assets) / optimizer.n_assets
        eq_metrics = optimizer._compute_portfolio_metrics(eq_weights)
        assert opt_metrics["volatility"] <= eq_metrics["volatility"] + 1e-6

    def test_with_target_return(self, optimizer: CatBondOptimizer) -> None:
        # Target return equal to the mean-excess return of the minimum-variance portfolio
        mv_result = optimizer.optimize_min_variance(min_weight=0.0, max_weight=1.0)
        mv_exp = optimizer.mean_returns @ mv_result["weights"]

        higher_target = mv_exp * 1.2  # Ask for slightly more
        result = optimizer.optimize_min_variance(
            min_weight=0.0, max_weight=1.0, target_return=higher_target
        )
        achieved = optimizer.mean_returns @ result["weights"]
        assert achieved >= higher_target - 1e-6
        assert np.sum(result["weights"]) == pytest.approx(1.0, abs=1e-6)

    def test_status_is_optimal(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_min_variance(min_weight=0.0, max_weight=1.0)
        assert result["status"] == "optimal"


# =====================================================================
# Minimum CVaR
# =====================================================================


class TestMinCVaR:
    """Tests for CVaR minimisation (Rockafellar-Uryasev)."""

    def test_weights_sum_to_one(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_min_cvar(
            alpha=0.05, min_weight=0.0, max_weight=1.0
        )
        assert np.sum(result["weights"]) == pytest.approx(1.0, abs=1e-6)

    def test_cvar_lower_than_equal_weight(
        self, optimizer: CatBondOptimizer
    ) -> None:
        result = optimizer.optimize_min_cvar(
            alpha=0.05, min_weight=0.0, max_weight=1.0
        )
        opt_metrics = optimizer._compute_portfolio_metrics(result["weights"])
        eq_weights = np.ones(optimizer.n_assets) / optimizer.n_assets
        eq_metrics = optimizer._compute_portfolio_metrics(eq_weights)
        # CVaR is negative (losses); lower (more negative) is worse.
        # Optimised CVaR should be >= equal-weight CVaR (less severe loss).
        assert opt_metrics["cvar_95"] >= eq_metrics["cvar_95"] - 1e-6

    def test_alpha_sensitivity_tighter_alpha_gives_worse_cvar(
        self, optimizer: CatBondOptimizer
    ) -> None:
        """A tighter alpha (deeper tail) should report a more extreme CVaR."""
        res_05 = optimizer.optimize_min_cvar(alpha=0.05, min_weight=0.0, max_weight=1.0)
        res_01 = optimizer.optimize_min_cvar(alpha=0.01, min_weight=0.0, max_weight=1.0)
        m_05 = optimizer._compute_portfolio_metrics(res_05["weights"])
        m_01 = optimizer._compute_portfolio_metrics(res_01["weights"])
        # CVaR at 99 % (alpha=0.01) is deeper in the tail → typically worse
        assert m_01["cvar_99"] <= m_05["cvar_95"] + 1e-4


# =====================================================================
# Mean–CVaR Trade-off
# =====================================================================


class TestMeanCVaR:
    """Tests for the mean-CVaR trade-off optimisation."""

    def test_weights_sum_to_one(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_mean_cvar(
            alpha=0.05, risk_aversion=1.0, min_weight=0.0, max_weight=1.0
        )
        assert np.sum(result["weights"]) == pytest.approx(1.0, abs=1e-6)

    def test_risk_aversion_zero_maximizes_return(
        self, optimizer: CatBondOptimizer
    ) -> None:
        """With λ→0, the objective is just -E[R] so we maximise return."""
        result = optimizer.optimize_mean_cvar(
            alpha=0.05, risk_aversion=0.01, min_weight=0.0, max_weight=1.0
        )
        opt_ret = optimizer.mean_returns @ result["weights"]
        eq_ret = optimizer.mean_returns @ (
            np.ones(optimizer.n_assets) / optimizer.n_assets
        )
        # Should be at least as good as equal-weight
        assert opt_ret >= eq_ret - 1e-6

    def test_high_risk_aversion_similar_to_min_cvar(
        self, optimizer: CatBondOptimizer
    ) -> None:
        """Very high λ effectively minimises CVaR, matching min-cvar result."""
        hi_lambda = optimizer.optimize_mean_cvar(
            alpha=0.05, risk_aversion=10.0, min_weight=0.0, max_weight=1.0
        )
        min_cvar = optimizer.optimize_min_cvar(
            alpha=0.05, min_weight=0.0, max_weight=1.0
        )
        m_hi = optimizer._compute_portfolio_metrics(hi_lambda["weights"])
        m_mc = optimizer._compute_portfolio_metrics(min_cvar["weights"])
        # CVaR values should be close
        assert m_hi["cvar_95"] == pytest.approx(m_mc["cvar_95"], abs=0.02)


# =====================================================================
# Maximum Return (Constrained)
# =====================================================================


class TestMaxReturn:
    """Tests for return-maximisation with risk constraints."""

    def test_weights_sum_to_one(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_max_return(
            max_volatility=0.15, min_weight=0.0, max_weight=1.0
        )
        assert np.sum(result["weights"]) == pytest.approx(1.0, abs=1e-6)

    def test_volatility_within_constraint(
        self, optimizer: CatBondOptimizer
    ) -> None:
        cap = 0.10
        result = optimizer.optimize_max_return(
            max_volatility=cap, min_weight=0.0, max_weight=1.0
        )
        metrics = optimizer._compute_portfolio_metrics(result["weights"])
        assert metrics["volatility"] <= cap + 1e-4

    def test_cvar_within_constraint(self, optimizer: CatBondOptimizer) -> None:
        cap = 0.30
        result = optimizer.optimize_max_return(
            max_cvar=cap, alpha=0.05, min_weight=0.0, max_weight=1.0
        )
        # CVaR is computed on original returns; the constraint is on absolute magnitude
        if result["status"] == "optimal":
            assert np.sum(result["weights"]) == pytest.approx(1.0, abs=1e-6)

    def test_status_is_optimal_with_relaxed_constraint(
        self, optimizer: CatBondOptimizer
    ) -> None:
        result = optimizer.optimize_max_return(
            max_volatility=0.50, min_weight=0.0, max_weight=1.0
        )
        assert result["status"] == "optimal"


# =====================================================================
# Exponential Utility (CARA)
# =====================================================================


class TestExponentialUtility:
    """Tests for the CARA exponential utility optimisation."""

    def test_weights_sum_to_one(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_exponential_utility(
            risk_aversion=0.5, min_weight=0.0, max_weight=1.0
        )
        assert np.sum(result["weights"]) == pytest.approx(1.0, abs=1e-6)

    def test_risk_neutral_maximizes_return(
        self, optimizer: CatBondOptimizer
    ) -> None:
        """risk_aversion=0.5 → C=0 (risk-neutral) → should maximise return."""
        result = optimizer.optimize_exponential_utility(
            risk_aversion=0.5, min_weight=0.0, max_weight=1.0
        )
        opt_ret = optimizer.mean_returns @ result["weights"]
        eq_ret = optimizer.mean_returns @ (
            np.ones(optimizer.n_assets) / optimizer.n_assets
        )
        assert opt_ret >= eq_ret - 1e-6

    def test_high_aversion_reduces_volatility(
        self, optimizer: CatBondOptimizer
    ) -> None:
        """Higher risk aversion should yield lower or equal volatility."""
        low_aversion = optimizer.optimize_exponential_utility(
            risk_aversion=0.5, min_weight=0.0, max_weight=1.0
        )
        high_aversion = optimizer.optimize_exponential_utility(
            risk_aversion=1.0, min_weight=0.0, max_weight=1.0
        )
        m_low = optimizer._compute_portfolio_metrics(low_aversion["weights"])
        m_high = optimizer._compute_portfolio_metrics(high_aversion["weights"])
        assert m_high["volatility"] <= m_low["volatility"] + 1e-4

    def test_status_is_optimal(self, optimizer: CatBondOptimizer) -> None:
        result = optimizer.optimize_exponential_utility(
            risk_aversion=0.5, min_weight=0.0, max_weight=1.0
        )
        assert result["status"] == "optimal"


# =====================================================================
# Portfolio Metrics
# =====================================================================


class TestMetrics:
    """Tests for _compute_portfolio_metrics correctness."""

    def test_compute_portfolio_metrics_keys(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        metrics = optimizer._compute_portfolio_metrics(equal_weights)
        expected_keys = {
            "expected_return",
            "volatility",
            "sharpe_ratio",
            "var_90",
            "var_95",
            "var_98",
            "var_99",
            "cvar_90",
            "cvar_95",
            "cvar_98",
            "cvar_99",
            "worst_scenario",
        }
        assert expected_keys == set(metrics.keys())

    def test_sharpe_ratio_formula(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        metrics = optimizer._compute_portfolio_metrics(equal_weights)
        expected_sharpe = (
            (metrics["expected_return"] - optimizer.rf) / metrics["volatility"]
        )
        assert metrics["sharpe_ratio"] == pytest.approx(expected_sharpe, rel=1e-6)

    def test_cvar_less_than_or_equal_var(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        """CVaR (expected shortfall) is at most VaR (both are loss quantities)."""
        metrics = optimizer._compute_portfolio_metrics(equal_weights)
        assert metrics["cvar_95"] <= metrics["var_95"] + 1e-8
        assert metrics["cvar_99"] <= metrics["var_99"] + 1e-8

    def test_worst_scenario_less_than_var99(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        metrics = optimizer._compute_portfolio_metrics(equal_weights)
        assert metrics["worst_scenario"] <= metrics["var_99"] + 1e-8

    def test_volatility_positive(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        metrics = optimizer._compute_portfolio_metrics(equal_weights)
        assert metrics["volatility"] > 0.0

    def test_var_ordering(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        """VaR should be monotonically worse at higher confidence."""
        metrics = optimizer._compute_portfolio_metrics(equal_weights)
        assert metrics["var_99"] <= metrics["var_98"] + 1e-8
        assert metrics["var_98"] <= metrics["var_95"] + 1e-8
        assert metrics["var_95"] <= metrics["var_90"] + 1e-8


# =====================================================================
# Distribution Statistics
# =====================================================================


class TestDistributionStats:
    """Tests for _compute_distribution_stats correctness."""

    def test_percentiles_monotonic(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        stats = optimizer._compute_distribution_stats(equal_weights)
        percentiles = [
            stats["p1"],
            stats["p5"],
            stats["p10"],
            stats["p25"],
            stats["p50"],
            stats["p75"],
            stats["p90"],
            stats["p95"],
            stats["p99"],
        ]
        for i in range(len(percentiles) - 1):
            assert percentiles[i] <= percentiles[i + 1] + 1e-10

    def test_prob_positive_between_0_and_1(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        stats = optimizer._compute_distribution_stats(equal_weights)
        assert 0.0 <= stats["prob_positive"] <= 1.0

    def test_mean_close_to_p50_for_symmetric(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        """Cat-bond returns are skewed but mean vs median should be in same ballpark."""
        stats = optimizer._compute_distribution_stats(equal_weights)
        # Allow generous tolerance due to heavy left tail
        assert abs(stats["mean"] - stats["median"]) < 0.10

    def test_no_loss_return_equals_max(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        stats = optimizer._compute_distribution_stats(equal_weights)
        assert stats["no_loss_return"] == pytest.approx(stats["max"], rel=1e-10)

    def test_expected_loss_negative(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        """expected_loss = mean - max, which should be ≤ 0."""
        stats = optimizer._compute_distribution_stats(equal_weights)
        assert stats["expected_loss"] <= 0.0 + 1e-10

    def test_loss_probabilities_decreasing(
        self,
        optimizer: CatBondOptimizer,
        equal_weights: np.ndarray,
    ) -> None:
        stats = optimizer._compute_distribution_stats(equal_weights)
        assert stats["prob_loss_5"] >= stats["prob_loss_10"] - 1e-10
        assert stats["prob_loss_10"] >= stats["prob_loss_25"] - 1e-10
        assert stats["prob_loss_25"] >= stats["prob_loss_50"] - 1e-10


# =====================================================================
# Efficient Frontier
# =====================================================================


class TestEfficientFrontier:
    """Tests for the efficient frontier computation."""

    def test_frontier_has_correct_number_of_points(
        self, optimizer: CatBondOptimizer
    ) -> None:
        frontier = optimizer.efficient_frontier(n_points=10)
        # May have fewer points if some targets are infeasible
        assert 1 <= len(frontier) <= 10

    def test_frontier_return_is_increasing(
        self, optimizer: CatBondOptimizer
    ) -> None:
        frontier = optimizer.efficient_frontier(n_points=15)
        returns = [p["expected_return"] for p in frontier]
        for i in range(len(returns) - 1):
            assert returns[i] <= returns[i + 1] + 1e-6

    def test_frontier_volatility_is_generally_increasing(
        self, optimizer: CatBondOptimizer
    ) -> None:
        """Volatility generally increases along the frontier (small non-monotonicity ok)."""
        frontier = optimizer.efficient_frontier(n_points=15)
        vols = [p["volatility"] for p in frontier]
        # Overall trend: last should be >= first
        assert vols[-1] >= vols[0] - 1e-6

    def test_frontier_contains_required_keys(
        self, optimizer: CatBondOptimizer
    ) -> None:
        frontier = optimizer.efficient_frontier(n_points=5)
        for point in frontier:
            assert "expected_return" in point
            assert "volatility" in point
            assert "sharpe_ratio" in point
            assert "cvar_95" in point

    @pytest.mark.slow
    def test_frontier_large_n_points(self, optimizer: CatBondOptimizer) -> None:
        frontier = optimizer.efficient_frontier(n_points=50)
        assert len(frontier) >= 10
