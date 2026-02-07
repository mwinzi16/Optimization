"""Shared pytest fixtures for the portfolio optimizer test suite.

Provides:
    - Flask test app with real sample data
    - Flask test client
    - API / auth header helpers
    - Synthetic CSV data for upload testing
    - CatBondOptimizer and helper fixtures for unit tests
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.config import Settings
from app.services.optimizer import CatBondOptimizer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _generate_cat_bond_returns(
    n_assets: int = 5,
    n_scenarios: int = 500,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a deterministic DataFrame of realistic cat-bond returns.

    Most scenarios receive a coupon (~5 %).  A small fraction suffer
    catastrophe losses ranging from -10 % to -80 %.
    """
    rng = np.random.default_rng(seed)
    asset_names = [f"CatBond_{chr(65 + i)}" for i in range(n_assets)]

    data: dict[str, np.ndarray] = {}
    for i, name in enumerate(asset_names):
        coupon = 0.04 + 0.02 * (i / max(n_assets - 1, 1))
        returns = rng.normal(loc=coupon, scale=0.005, size=n_scenarios)

        n_losses = int(n_scenarios * 0.08)
        loss_indices = rng.choice(n_scenarios, size=n_losses, replace=False)
        losses = rng.uniform(-0.80, -0.10, size=n_losses)
        returns[loss_indices] = losses

        data[name] = returns

    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Application fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def app() -> Flask:
    """Create a Flask app configured for testing with real sample data."""
    from app import create_app

    settings = Settings(
        SECRET_KEY="test-secret",
        ALLOW_ANONYMOUS=True,
        DATA_PATH=str(Path(__file__).parent.parent / "data" / "scenario_returns.csv"),
    )
    application = create_app(settings)
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def api_headers() -> dict[str, str]:
    """Standard JSON request headers."""
    return {"Content-Type": "application/json"}


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Headers with a valid API key for auth-protected endpoints."""
    return {"X-API-Key": "test-key", "Content-Type": "application/json"}


@pytest.fixture()
def sample_csv_bytes() -> bytes:
    """Create a minimal valid CSV in memory (3 asset columns, 150 rows)."""
    rng = np.random.default_rng(42)
    data = rng.normal(loc=0.05, scale=0.10, size=(150, 3))
    df = pd.DataFrame(data, columns=["Bond_A", "Bond_B", "Bond_C"])
    buf = io.BytesIO()
    df.to_csv(buf, index=True)
    return buf.getvalue()


@pytest.fixture()
def sample_invalid_csv_bytes() -> bytes:
    """Create a CSV that fails validation (only 1 numeric column)."""
    rng = np.random.default_rng(99)
    data = rng.normal(loc=0.05, scale=0.10, size=(150, 1))
    df = pd.DataFrame(data, columns=["Only_Asset"])
    buf = io.BytesIO()
    df.to_csv(buf, index=True)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Non-anonymous app (for auth tests)
# ---------------------------------------------------------------------------


@pytest.fixture()
def nonanon_app() -> Flask:
    """Create a Flask app with ALLOW_ANONYMOUS=False for auth tests."""
    from app import create_app

    settings = Settings(
        SECRET_KEY="test-secret",
        ALLOW_ANONYMOUS=False,
        API_KEY="test-secret-key",
        DATA_PATH=str(Path(__file__).parent.parent / "data" / "scenario_returns.csv"),
    )
    application = create_app(settings)
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def nonanon_client(nonanon_app: Flask) -> FlaskClient:
    """Flask test client for the non-anonymous app."""
    return nonanon_app.test_client()


# ---------------------------------------------------------------------------
# Optimizer unit-test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sample_returns() -> pd.DataFrame:
    """Deterministic 5-asset, 500-scenario cat-bond returns DataFrame."""
    return _generate_cat_bond_returns()


@pytest.fixture(scope="session")
def optimizer(sample_returns: pd.DataFrame) -> CatBondOptimizer:
    """CatBondOptimizer built from the session-scoped sample returns."""
    return CatBondOptimizer(sample_returns, risk_free_rate=0.02)


@pytest.fixture(scope="session")
def equal_weights(sample_returns: pd.DataFrame) -> np.ndarray:
    """Equal-weight vector matching the number of sample assets."""
    n = sample_returns.shape[1]
    return np.ones(n) / n
