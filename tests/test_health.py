"""Tests for GET /api/v1/health endpoint."""

from __future__ import annotations

from flask.testing import FlaskClient


class TestHealth:
    """Health check endpoint tests."""

    def test_health_returns_200(self, client: FlaskClient) -> None:
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_contains_status(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/health").get_json()
        assert body["data"]["status"] == "healthy"

    def test_health_data_loaded_true(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/health").get_json()
        assert body["data"]["data_loaded"] is True

    def test_health_shows_data_shape(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/health").get_json()
        shape = body["data"]["data_shape"]
        assert "scenarios" in shape
        assert "assets" in shape
        assert shape["scenarios"] > 0
        assert shape["assets"] > 0

    def test_health_envelope_structure(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/health").get_json()
        assert "data" in body
        assert "meta" in body
        assert "errors" in body

    def test_health_contains_version(self, client: FlaskClient) -> None:
        body = client.get("/api/v1/health").get_json()
        assert "version" in body["data"]
