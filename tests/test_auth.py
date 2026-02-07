"""Tests for API key authentication."""

from __future__ import annotations

from flask import Flask
from flask.testing import FlaskClient


class TestAuth:
    """Authentication tests using the default anonymous-allowed app."""

    def test_anonymous_allowed_when_configured(self, client: FlaskClient) -> None:
        """Protected endpoints should succeed without auth when ALLOW_ANONYMOUS=True."""
        resp = client.post("/api/v1/optimize", json={
            "method": "Minimum Variance",
            "min_weight": 0.0,
            "max_weight": 1.0,
        })
        assert resp.status_code == 200


class TestAuthRequired:
    """Authentication tests with ALLOW_ANONYMOUS=False."""

    def test_api_key_required_when_not_anonymous(
        self, nonanon_client: FlaskClient
    ) -> None:
        """Protected endpoints need X-API-Key when ALLOW_ANONYMOUS=False."""
        resp = nonanon_client.post("/api/v1/optimize", json={
            "method": "Minimum Variance",
            "min_weight": 0.0,
            "max_weight": 1.0,
        })
        assert resp.status_code == 401

    def test_invalid_api_key_returns_401(
        self, nonanon_client: FlaskClient
    ) -> None:
        resp = nonanon_client.post(
            "/api/v1/optimize",
            json={"method": "Minimum Variance"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert resp.status_code == 401

    def test_missing_api_key_returns_401(
        self, nonanon_client: FlaskClient
    ) -> None:
        resp = nonanon_client.post(
            "/api/v1/reset",
        )
        assert resp.status_code == 401

    def test_valid_api_key_returns_200(
        self, nonanon_client: FlaskClient
    ) -> None:
        resp = nonanon_client.post(
            "/api/v1/reset",
            headers={"X-API-Key": "test-secret-key"},
        )
        assert resp.status_code == 200
