"""Tests for the web blueprint (HTMX-driven UI routes)."""

from __future__ import annotations

from flask.testing import FlaskClient


class TestWebIndex:
    """Tests for the main index page."""

    def test_index_returns_200(self, client: FlaskClient) -> None:
        resp = client.get("/")
        assert resp.status_code == 200

    def test_index_contains_form_elements(self, client: FlaskClient) -> None:
        resp = client.get("/")
        html = resp.data.decode()
        # The page should contain key form elements
        assert "method" in html.lower() or "optimize" in html.lower()
        assert "<form" in html.lower() or "hx-post" in html.lower()


class TestWebOptimize:
    """Tests for the form-based optimize endpoint."""

    def test_optimize_via_form_returns_results(self, client: FlaskClient) -> None:
        resp = client.post(
            "/optimize",
            data={
                "method": "Maximum Sharpe Ratio",
                "risk_free_rate": "4.0",
                "min_weight": "0.0",
                "max_weight": "100.0",
                "cvar_alpha": "95",
                "risk_aversion": "1.0",
                "constraint_type": "volatility",
                "max_volatility": "15.0",
                "max_cvar": "25.0",
                "exp_risk_aversion": "0.5",
            },
        )
        assert resp.status_code == 200
        html = resp.data.decode()
        # Results partial should contain optimization output
        assert len(html) > 100  # Non-trivial response


class TestMethodParams:
    """Tests for the method-params HTMX endpoint."""

    def test_method_params_endpoint_returns_partial(
        self, client: FlaskClient
    ) -> None:
        resp = client.get("/method-params/Minimum%20CVaR")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert len(html) > 0

    def test_method_params_maximum_sharpe(self, client: FlaskClient) -> None:
        resp = client.get("/method-params/Maximum%20Sharpe%20Ratio")
        assert resp.status_code == 200


class TestWebReset:
    """Tests for the web reset endpoint."""

    def test_reset_returns_data_status(self, client: FlaskClient) -> None:
        resp = client.post("/reset")
        assert resp.status_code == 200
        html = resp.data.decode()
        # Should return a data-status partial
        assert len(html) > 0
