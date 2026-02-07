"""Tests for GET /api/v1/assets endpoint."""

from __future__ import annotations

from flask.testing import FlaskClient


class TestAssets:
    """Asset listing endpoint tests."""

    def test_assets_returns_200(self, client: FlaskClient) -> None:
        resp = client.get("/api/v1/assets")
        assert resp.status_code == 200

    def test_assets_returns_list(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/assets").get_json()
        assert isinstance(body["data"], list)
        assert len(body["data"]) > 0

    def test_assets_has_expected_fields(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/assets").get_json()
        required_fields = {
            "name",
            "expected_return",
            "volatility",
            "var_90",
            "var_95",
            "var_99",
            "cvar_95",
        }
        for asset in body["data"]:
            assert required_fields.issubset(set(asset.keys()))

    def test_assets_meta_count(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/assets").get_json()
        assert body["meta"]["count"] == len(body["data"])

    def test_assets_has_no_loss_return_and_expected_loss(
        self, client: FlaskClient
    ) -> None:
        body = client.get("/api/v1/assets").get_json()
        for asset in body["data"]:
            assert "no_loss_return" in asset
            assert "expected_loss" in asset
