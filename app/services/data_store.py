"""Thread-safe data store for shared optimizer state."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

import pandas as pd

from .optimizer import CatBondOptimizer
from ..utils.cache import optimization_cache, frontier_cache


class _DataStore:
    """Thread-safe container for shared optimizer state."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._returns_df: Optional[pd.DataFrame] = None
        self._optimizer: Optional[CatBondOptimizer] = None

    @property
    def returns_df(self) -> Optional[pd.DataFrame]:
        with self._lock:
            return self._returns_df

    @property
    def optimizer(self) -> Optional[CatBondOptimizer]:
        with self._lock:
            return self._optimizer

    def update(self, returns_df: pd.DataFrame, risk_free_rate: float = 0.0) -> None:
        with self._lock:
            self._returns_df = returns_df
            self._optimizer = CatBondOptimizer(returns_df, risk_free_rate=risk_free_rate)
        optimization_cache.clear()
        frontier_cache.clear()

    def get_optimizer(self, risk_free_rate: float) -> CatBondOptimizer:
        """Get an optimizer with the specified risk-free rate.

        Creates a new instance locally — does NOT mutate global state.
        """
        with self._lock:
            if self._returns_df is None:
                raise ValueError("Data not loaded")
            return CatBondOptimizer(self._returns_df.copy(), risk_free_rate=risk_free_rate)


data_store = _DataStore()


def load_data(data_path: str) -> None:
    """Load scenario returns from CSV file into the data store."""
    path = Path(data_path)
    if path.exists():
        df = pd.read_csv(path, index_col=0)
        data_store.update(df, risk_free_rate=0.0)
    else:
        import logging
        logging.getLogger(__name__).warning("Data file not found: %s", data_path)
