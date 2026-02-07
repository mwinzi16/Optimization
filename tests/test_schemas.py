"""Tests for Pydantic request/response schemas and validation helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.schemas.optimization import (
    ValidatedOptimizationRequest,
    sanitize_column_names,
    validate_file_extension,
)


class TestValidatedOptimizationRequest:
    """Tests for the Pydantic request model."""

    def test_valid_request(self) -> None:
        req = ValidatedOptimizationRequest(
            method="Maximum Sharpe Ratio",
            min_weight=0.0,
            max_weight=1.0,
            risk_free_rate=0.02,
        )
        assert req.method == "Maximum Sharpe Ratio"

    def test_invalid_method_rejected(self) -> None:
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(method="FooBar Strategy")

    def test_min_weight_exceeds_max_weight_rejected(self) -> None:
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(
                method="Minimum Variance",
                min_weight=0.6,
                max_weight=0.2,
            )

    def test_default_values(self) -> None:
        req = ValidatedOptimizationRequest(method="Minimum Variance")
        assert req.min_weight == 0.0
        assert req.max_weight == 1.0
        assert req.risk_free_rate == 0.0
        assert req.cvar_alpha == 0.05
        assert req.risk_aversion == 1.0
        assert req.exp_risk_aversion == 0.5
        assert req.constraint_type == "volatility"

    def test_all_valid_methods_accepted(self) -> None:
        methods = [
            "Maximum Sharpe Ratio",
            "Minimum Variance",
            "Minimum CVaR",
            "Mean-CVaR Trade-off",
            "Maximum Return (Constrained)",
            "Exponential Utility (CARA)",
        ]
        for m in methods:
            req = ValidatedOptimizationRequest(method=m)
            assert req.method == m


class TestSanitizeColumnNames:
    """Tests for sanitize_column_names."""

    def test_sanitize_column_names(self) -> None:
        result = sanitize_column_names(["col\n1", "col\r\n2"])
        assert result == ["col 1", "col 2"]

    def test_handles_spaces(self) -> None:
        result = sanitize_column_names(["  spaced  out  "])
        assert result == ["spaced out"]

    def test_truncates_long_names(self) -> None:
        long_name = "A" * 200
        result = sanitize_column_names([long_name])
        assert len(result[0]) <= 100

    def test_empty_string_gets_default(self) -> None:
        result = sanitize_column_names(["", "valid"])
        assert result[0].startswith("Asset_")
        assert result[1] == "valid"


class TestValidateFileExtension:
    """Tests for validate_file_extension."""

    def test_validate_file_extension_csv(self) -> None:
        ok, info = validate_file_extension("data.csv")
        assert ok is True
        assert info == "csv"

    def test_validate_file_extension_xlsx(self) -> None:
        ok, info = validate_file_extension("data.xlsx")
        assert ok is True
        assert info == "xlsx"

    def test_validate_file_extension_invalid(self) -> None:
        ok, info = validate_file_extension("data.txt")
        assert ok is False
        assert "Unsupported" in info

    def test_validate_file_extension_empty(self) -> None:
        ok, _ = validate_file_extension("")
        assert ok is False
