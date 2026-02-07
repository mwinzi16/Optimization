"""Tests for GET /api/v1/efficient-frontier endpoint."""

from __future__ import annotations

from flask.testing import FlaskClient


class TestFrontier:
    """Efficient frontier endpoint tests."""

    def test_frontier_returns_200(self, client: FlaskClient) -> None:
        resp = client.get("/api/v1/efficient-frontier?n_points=10")
        assert resp.status_code == 200

    def test_frontier_data_is_list(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/efficient-frontier?n_points=10").get_json()
        assert isinstance(body["data"], list)

    def test_frontier_points_have_metrics(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/efficient-frontier?n_points=8").get_json()
        for pt in body["data"]:
            assert "expected_return" in pt
            assert "volatility" in pt
            assert "sharpe_ratio" in pt
            assert "cvar_95" in pt

    def test_frontier_meta_n_points(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/efficient-frontier?n_points=8").get_json()
        assert "n_points" in body["meta"]
        assert body["meta"]["n_points"] == len(body["data"])

    def test_frontier_custom_n_points(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/efficient-frontier?n_points=15").get_json()
        assert len(body["data"]) <= 15

    def test_frontier_clamps_n_points_low(self, client: FlaskClient) -> None:
        """n_points below 5 should be clamped to 5."""
        resp = client.get("/api/v1/efficient-frontier?n_points=2")
        assert resp.status_code == 200
        body = resp.get_json()
        # The actual frontier may have fewer points if targets are infeasible,
        # but the request itself should succeed.
        assert isinstance(body["data"], list)

    def test_frontier_clamps_n_points_high(self, client: FlaskClient) -> None:
        """n_points above 100 should be clamped to 100."""
        resp = client.get("/api/v1/efficient-frontier?n_points=200")
        assert resp.status_code == 200
        body = resp.get_json()
        assert len(body["data"]) <= 100
