"""Additional portfolio statistics computation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_additional_stats(portfolio_returns: np.ndarray, rf: float = 0.04) -> dict:
    """Compute additional portfolio statistics including Sortino, percentiles, etc."""
    returns = portfolio_returns
    
    prob_positive = float((returns > 0).mean())
    prob_loss_5 = float((returns < -0.05).mean())
    prob_loss_10 = float((returns < -0.10).mean())
    prob_loss_25 = float((returns < -0.25).mean())
    prob_loss_50 = float((returns < -0.50).mean())
    
    p1 = float(np.percentile(returns, 1))
    p5 = float(np.percentile(returns, 5))
    p10 = float(np.percentile(returns, 10))
    p25 = float(np.percentile(returns, 25))
    p50 = float(np.percentile(returns, 50))
    p75 = float(np.percentile(returns, 75))
    p90 = float(np.percentile(returns, 90))
    p95 = float(np.percentile(returns, 95))
    p99 = float(np.percentile(returns, 99))
    
    skewness = float(pd.Series(returns).skew())
    kurtosis = float(pd.Series(returns).kurtosis())
    
    downside_diff = np.minimum(returns - rf, 0)
    downside_dev = float(np.sqrt(np.mean(downside_diff ** 2)))
    
    excess_return = float(np.mean(returns)) - rf
    sortino = float(excess_return / downside_dev) if downside_dev > 0 else 0.0
    
    return {
        "prob_positive": prob_positive, "prob_loss_5": prob_loss_5,
        "prob_loss_10": prob_loss_10, "prob_loss_25": prob_loss_25,
        "prob_loss_50": prob_loss_50,
        "p1": p1, "p5": p5, "p10": p10, "p25": p25, "p50": p50,
        "p75": p75, "p90": p90, "p95": p95, "p99": p99,
        "skewness": skewness, "kurtosis": kurtosis,
        "downside_dev": downside_dev, "sortino_ratio": sortino,
    }
