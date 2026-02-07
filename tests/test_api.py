"""
Integration tests for the Flask API endpoints — Portfolio Optimizer.

Uses the Flask test client (synchronous) instead of the old httpx async
approach that targeted the removed FastAPI backend.
"""

from __future__ import annotations

import io

import numpy as np
import pandas as pd
import pytest
from flask.testing import FlaskClient


# =====================================================================
# Health
# =====================================================================


class TestHealth:
    """Tests for GET /api/v1/health."""

    def test_health_returns_200(self, client: FlaskClient) -> None:
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_envelope_structure(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/health").get_json()
        assert "data" in body
        assert "meta" in body
        assert "errors" in body

    def test_health_shows_data_loaded(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/health").get_json()
        assert body["data"]["data_loaded"] is True
        assert body["data"]["status"] == "healthy"

    def test_health_contains_version(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/health").get_json()
        assert "version" in body["data"]


# =====================================================================
# Assets
# =====================================================================


class TestAssets:
    """Tests for GET /api/v1/assets."""

    def test_get_assets_returns_list(self, client: FlaskClient) -> None:
        resp = client.get("/api/v1/assets")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert isinstance(data, list)
        assert len(data) > 0

    def test_asset_info_has_required_fields(self, client: FlaskClient) -> None:
        data = client.get("/api/v1/assets").get_json()["data"]
        required = {
            "name", "expected_return", "no_loss_return", "expected_loss",
            "volatility", "var_90", "var_95", "var_99", "cvar_95",
        }
        for asset in data:
            assert required.issubset(set(asset.keys()))

    def test_asset_count_in_meta(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/assets").get_json()
        assert body["meta"]["count"] == len(body["data"])


# =====================================================================
# Optimize
# =====================================================================


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


class TestOptimize:
    """Tests for POST /api/v1/optimize."""

    def test_optimize_max_sharpe(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize", json={**_BASE_REQUEST, "method": "Maximum Sharpe Ratio"}
        )
        assert resp.status_code == 200

    def test_optimize_min_variance(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize", json={**_BASE_REQUEST, "method": "Minimum Variance"}
        )
        assert resp.status_code == 200

    def test_optimize_min_cvar(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize", json={**_BASE_REQUEST, "method": "Minimum CVaR"}
        )
        assert resp.status_code == 200

    def test_optimize_mean_cvar(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={**_BASE_REQUEST, "method": "Mean-CVaR Trade-off"},
        )
        assert resp.status_code == 200

    def test_optimize_max_return_vol_constraint(self, client: FlaskClient) -> None:
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

    def test_optimize_max_return_cvar_constraint(self, client: FlaskClient) -> None:
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

    def test_optimize_exponential_utility(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={
                **_BASE_REQUEST,
                "method": "Exponential Utility (CARA)",
                "exp_risk_aversion": 0.7,
            },
        )
        assert resp.status_code == 200

    def test_optimize_invalid_method_returns_422(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={**_BASE_REQUEST, "method": "NonExistentMethod"},
        )
        assert resp.status_code == 422

    def test_optimize_invalid_weights_returns_422(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/optimize",
            json={**_BASE_REQUEST, "min_weight": 0.9, "max_weight": 0.1},
        )
        assert resp.status_code == 422

    def test_response_has_envelope_structure(self, client: FlaskClient) -> None:
        body = client.post("/api/v1/optimize", json=_BASE_REQUEST).get_json()
        assert "data" in body
        assert "meta" in body
        assert "errors" in body

    def test_response_weights_sum_to_one(self, client: FlaskClient) -> None:
        body = client.post("/api/v1/optimize", json=_BASE_REQUEST).get_json()
        weights = body["data"]["weights"]
        assert sum(weights.values()) == pytest.approx(1.0, abs=1e-4)

    def test_response_contains_metrics(self, client: FlaskClient) -> None:
        body = client.post("/api/v1/optimize", json=_BASE_REQUEST).get_json()
        metrics = body["data"]["metrics"]
        assert "expected_return" in metrics
        assert "volatility" in metrics
        assert "sharpe_ratio" in metrics

    def test_response_contains_distribution_stats(
        self, client: FlaskClient
    ) -> None:
        body = client.post("/api/v1/optimize", json=_BASE_REQUEST).get_json()
        assert "distribution_stats" in body["data"]
        assert "portfolio_returns" in body["data"]


# =====================================================================
# Efficient Frontier
# =====================================================================


class TestEfficientFrontier:
    """Tests for GET /api/v1/efficient-frontier."""

    def test_frontier_returns_list(self, client: FlaskClient) -> None:
        resp = client.get("/api/v1/efficient-frontier?n_points=10")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert isinstance(data, list)

    def test_frontier_n_points_bounded(self, client: FlaskClient) -> None:
        resp = client.get("/api/v1/efficient-frontier?n_points=10")
        data = resp.get_json()["data"]
        assert len(data) <= 10

    def test_frontier_clamped_low(self, client: FlaskClient) -> None:
        """n_points < 5 gets clamped to 5."""
        resp = client.get("/api/v1/efficient-frontier?n_points=2")
        assert resp.status_code == 200

    def test_frontier_clamped_high(self, client: FlaskClient) -> None:
        """n_points > 100 gets clamped to 100."""
        resp = client.get("/api/v1/efficient-frontier?n_points=200")
        assert resp.status_code == 200

    def test_frontier_with_custom_params(self, client: FlaskClient) -> None:
        resp = client.get(
            "/api/v1/efficient-frontier",
            query_string={"min_weight": 0.01, "max_weight": 0.5, "n_points": 8},
        )
        assert resp.status_code == 200

    def test_frontier_point_structure(self, client: FlaskClient) -> None:
        data = client.get("/api/v1/efficient-frontier?n_points=5").get_json()["data"]
        for pt in data:
            assert "expected_return" in pt
            assert "volatility" in pt
            assert "sharpe_ratio" in pt
            assert "cvar_95" in pt


# =====================================================================
# Upload
# =====================================================================


def _make_csv_bytes(n_assets: int = 5, n_scenarios: int = 200) -> bytes:
    """Create a minimal valid CSV file in-memory."""
    rng = np.random.default_rng(99)
    cols = [f"Asset_{i}" for i in range(n_assets)]
    df = pd.DataFrame(
        rng.normal(0.04, 0.02, size=(n_scenarios, n_assets)),
        columns=cols,
    )
    buf = io.BytesIO()
    df.to_csv(buf)
    return buf.getvalue()


class TestUpload:
    """Tests for POST /api/v1/upload."""

    def test_upload_valid_csv(self, client: FlaskClient) -> None:
        csv_bytes = _make_csv_bytes()
        resp = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(csv_bytes), "returns.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["status"] == "success"
        assert body["data"]["n_assets"] == 5

    def test_upload_invalid_format_returns_error(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(b"junk"), "bad.txt")},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (400, 422)

    def test_upload_empty_file_returns_error(self, client: FlaskClient) -> None:
        resp = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(b""), "empty.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (400, 422, 500)

    def test_upload_too_few_assets_returns_error(self, client: FlaskClient) -> None:
        csv_bytes = _make_csv_bytes(n_assets=1, n_scenarios=200)
        resp = client.post(
            "/api/v1/upload",
            data={"file": (io.BytesIO(csv_bytes), "returns.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (400, 422)


# =====================================================================
# Reset
# =====================================================================


class TestReset:
    """Tests for POST /api/v1/reset."""

    def test_reset_restores_sample_data(self, client: FlaskClient) -> None:
        resp = client.post("/api/v1/reset")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["data"]["status"] == "success"

    def test_reset_then_health_shows_loaded(self, client: FlaskClient) -> None:
        client.post("/api/v1/reset")
        health = client.get("/api/v1/health").get_json()
        assert health["data"]["data_loaded"] is True

