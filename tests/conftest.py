"""
Shared pytest fixtures for the portfolio optimizer test suite.

Provides:
    - FastAPI async test client (httpx)
    - Deterministic sample returns DataFrame (5 assets, 500 scenarios)
    - Pre-built CatBondOptimizer instance
    - Equal-weight portfolio vector
"""

from __future__ import annotations

import os

# MUST be set before any backend imports so that config.ALLOW_ANONYMOUS is True
os.environ["ALLOW_ANONYMOUS"] = "true"

import numpy as np
import pandas as pd
import pytest
import httpx
from httpx import ASGITransport

from backend.api import CatBondOptimizer, app


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

    Args:
        n_assets: Number of bonds / columns.
        n_scenarios: Number of return scenarios / rows.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with shape (n_scenarios, n_assets).
    """
    rng = np.random.default_rng(seed)
    asset_names = [f"CatBond_{chr(65 + i)}" for i in range(n_assets)]  # A-E

    data: dict[str, np.ndarray] = {}
    for i, name in enumerate(asset_names):
        # Base coupon with slight noise per asset
        coupon = 0.04 + 0.02 * (i / max(n_assets - 1, 1))  # 4 %–6 %
        returns = rng.normal(loc=coupon, scale=0.005, size=n_scenarios)

        # Inject rare catastrophe losses (~8 % of scenarios)
        n_losses = int(n_scenarios * 0.08)
        loss_indices = rng.choice(n_scenarios, size=n_losses, replace=False)
        losses = rng.uniform(-0.80, -0.10, size=n_losses)
        returns[loss_indices] = losses

        data[name] = returns

    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Fixtures
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


@pytest.fixture
async def client():
    """Async httpx test client wired to the FastAPI application."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
