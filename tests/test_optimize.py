"""Tests for POST /api/v1/optimize endpoint — all 6 optimization methods."""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient


_BASE_REQUEST: dict = {
    "method": "Maximum Sharpe Ratio",
    "min_weight": 0.0,
    "max_weight": 1.0,
    "risk_free_rate": 0.02,
    "cvar_alpha": 0.05,
    "risk_aversion": 1.0,
    "exp_risk_aversion": 0.5,
    "constraint_type": "volatility",
    "cvar_constraint_alpha": 0.05,
}


class TestOptimizeStatus:
    """Verify each optimization method returns 200."""

    def test_optimize_max_sharpe_returns_200(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={**_BASE_REQUEST, "method": "Maximum Sharpe Ratio"},
        )
        assert resp.status_code == 200

    def test_optimize_min_variance_returns_200(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={**_BASE_REQUEST, "method": "Minimum Variance"},
        )
        assert resp.status_code == 200

    def test_optimize_min_cvar_returns_200(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={**_BASE_REQUEST, "method": "Minimum CVaR"},
        )
        assert resp.status_code == 200

    def test_optimize_mean_cvar_returns_200(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={**_BASE_REQUEST, "method": "Mean-CVaR Trade-off"},
        )
        assert resp.status_code == 200

    def test_optimize_max_return_volatility_constraint_returns_200(
        self, client: FlaskClient
    ) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={
                **_BASE_REQUEST,
                "method": "Maximum Return (Constrained)",
                "constraint_type": "volatility",
                "max_volatility": 0.15,
            },
        )
        assert resp.status_code == 200

    def test_optimize_max_return_cvar_constraint_returns_200(
        self, client: FlaskClient
    ) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={
                **_BASE_REQUEST,
                "method": "Maximum Return (Constrained)",
                "constraint_type": "cvar",
                "max_cvar": 0.25,
            },
        )
        assert resp.status_code == 200

    def test_optimize_exponential_utility_returns_200(
        self, client: FlaskClient
    ) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={
                **_BASE_REQUEST,
                "method": "Exponential Utility (CARA)",
                "exp_risk_aversion": 0.7,
            },
        )
        assert resp.status_code == 200


class TestOptimizeWeights:
    """Verify weight constraints in optimization responses."""

    @pytest.mark.parametrize(
        "method",
        [
            "Maximum Sharpe Ratio",
            "Minimum Variance",
            "Minimum CVaR",
            "Mean-CVaR Trade-off",
            "Exponential Utility (CARA)",
        ],
    )
    def test_optimize_weights_sum_to_one(
        self, client: FlaskClient, method: str
    ) -> None:
        body = client.post(
            "/api/v1/optimize", json={**_BASE_REQUEST, "method": method}
        ).get_json()
        weights = body["data"]["weights"]
        assert sum(weights.values()) == pytest.approx(1.0, abs=1e-4)

    def test_optimize_weights_within_bounds(self, client: FlaskClient) -> None:
        body = client.post(
            "/api/v1/optimize",
            json={**_BASE_REQUEST, "min_weight": 0.05, "max_weight": 0.60},
        ).get_json()
        weights = body["data"]["weights"]
        for w in weights.values():
            assert w >= 0.05 - 1e-4
            assert w <= 0.60 + 1e-4

    def test_optimize_with_custom_weight_bounds(self, client: FlaskClient) -> None:
        body = client.post(
            "/api/v1/optimize",
            json={
                **_BASE_REQUEST,
                "method": "Minimum Variance",
                "min_weight": 0.10,
                "max_weight": 0.40,
            },
        ).get_json()
        weights = body["data"]["weights"]
        assert sum(weights.values()) == pytest.approx(1.0, abs=1e-4)
        for w in weights.values():
            assert w >= 0.10 - 1e-4
            assert w <= 0.40 + 1e-4


class TestOptimizeResponse:
    """Verify the structure and content of optimization responses."""

    def test_optimize_response_has_metrics(self, client: FlaskClient) -> None:
        body = client.post("/api/v1/optimize", json=_BASE_REQUEST).get_json()
        metrics = body["data"]["metrics"]
        for key in ("expected_return", "volatility", "sharpe_ratio", "var_95", "cvar_95"):
            assert key in metrics

    def test_optimize_response_has_distribution_stats(
        self, client: FlaskClient
    ) -> None:
        body = client.post("/api/v1/optimize", json=_BASE_REQUEST).get_json()
        assert "distribution_stats" in body["data"]
        dist = body["data"]["distribution_stats"]
        for key in ("mean", "std", "skewness", "kurtosis", "prob_positive"):
            assert key in dist

    def test_optimize_response_has_scenario_returns(
        self, client: FlaskClient
    ) -> None:
        body = client.post("/api/v1/optimize", json=_BASE_REQUEST).get_json()
        data = body["data"]
        assert "best_scenario_returns" in data
        assert "var90_scenario_returns" in data
        assert "var95_scenario_returns" in data
        assert "var99_scenario_returns" in data

    def test_optimize_response_has_asset_mean_returns(
        self, client: FlaskClient
    ) -> None:
        body = client.post("/api/v1/optimize", json=_BASE_REQUEST).get_json()
        assert "asset_mean_returns" in body["data"]
        assert isinstance(body["data"]["asset_mean_returns"], dict)
        assert len(body["data"]["asset_mean_returns"]) > 0

    def test_optimize_response_has_portfolio_returns_list(
        self, client: FlaskClient
    ) -> None:
        body = client.post("/api/v1/optimize", json=_BASE_REQUEST).get_json()
        assert "portfolio_returns" in body["data"]
        assert isinstance(body["data"]["portfolio_returns"], list)
        assert len(body["data"]["portfolio_returns"]) > 0

    def test_optimize_response_envelope_structure(
        self, client: FlaskClient
    ) -> None:
        body = client.post("/api/v1/optimize", json=_BASE_REQUEST).get_json()
        assert "data" in body
        assert "meta" in body
        assert "errors" in body


class TestOptimizeErrors:
    """Verify error handling for invalid optimization requests."""

    def test_optimize_invalid_method_returns_422(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={**_BASE_REQUEST, "method": "NonExistentMethod"},
        )
        assert resp.status_code == 422

    def test_optimize_invalid_json_returns_400(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize",
            data="not json at all",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_optimize_min_weight_gt_max_weight_returns_422(
        self, client: FlaskClient
    ) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={**_BASE_REQUEST, "min_weight": 0.9, "max_weight": 0.1},
        )
        assert resp.status_code == 422
