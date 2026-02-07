"""Pydantic response models for API endpoints."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel


class OptimizationResponse(BaseModel):
    status: str
    method: str
    weights: Dict[str, float]
    metrics: Dict[str, float]
    portfolio_returns: List[float]
    distribution_stats: Dict[str, float]
    best_scenario_returns: Dict[str, float]
    var90_scenario_returns: Dict[str, float]
    var95_scenario_returns: Dict[str, float]
    var99_scenario_returns: Dict[str, float]
    asset_mean_returns: Dict[str, float]


class AssetInfo(BaseModel):
    name: str
    expected_return: float
    no_loss_return: float
    expected_loss: float
    volatility: float
    var_90: float
    var_95: float
    var_99: float
    cvar_95: float


class EfficientFrontierPoint(BaseModel):
    expected_return: float
    volatility: float
    sharpe_ratio: float
    cvar_95: float
