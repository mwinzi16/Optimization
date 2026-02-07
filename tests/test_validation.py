"""
Unit tests for input validation and sanitization helpers.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.schemas.optimization import (
    ValidatedOptimizationRequest,
    sanitize_column_names,
    validate_file_extension,
)


# =====================================================================
# ValidatedOptimizationRequest
# =====================================================================


class TestValidatedOptimizationRequest:
    """Tests for the Pydantic request model."""

    def test_valid_request_accepted(self) -> None:
        req = ValidatedOptimizationRequest(
            method="Maximum Sharpe Ratio",
            min_weight=0.0,
            max_weight=1.0,
            risk_free_rate=0.02,
        )
        assert req.method == "Maximum Sharpe Ratio"

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

    def test_invalid_method_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(method="FooBar Strategy")

    def test_min_greater_than_max_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(
                method="Minimum Variance",
                min_weight=0.6,
                max_weight=0.2,
            )

    def test_weight_out_of_range_raises(self) -> None:
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(
                method="Minimum Variance",
                min_weight=-0.5,
            )
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(
                method="Minimum Variance",
                max_weight=1.5,
            )

    def test_risk_free_rate_boundaries(self) -> None:
        # Valid edges
        ValidatedOptimizationRequest(method="Minimum Variance", risk_free_rate=-0.1)
        ValidatedOptimizationRequest(method="Minimum Variance", risk_free_rate=0.3)
        # Out of range
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(
                method="Minimum Variance", risk_free_rate=0.5
            )

    def test_cvar_alpha_boundaries(self) -> None:
        ValidatedOptimizationRequest(method="Minimum CVaR", cvar_alpha=0.01)
        ValidatedOptimizationRequest(method="Minimum CVaR", cvar_alpha=0.2)
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(method="Minimum CVaR", cvar_alpha=0.005)

    def test_constraint_type_validation(self) -> None:
        req = ValidatedOptimizationRequest(
            method="Maximum Return (Constrained)", constraint_type="cvar"
        )
        assert req.constraint_type == "cvar"
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(
                method="Maximum Return (Constrained)",
                constraint_type="invalid",
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

    def test_risk_aversion_range(self) -> None:
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(
                method="Mean-CVaR Trade-off", risk_aversion=0.0
            )
        with pytest.raises(PydanticValidationError):
            ValidatedOptimizationRequest(
                method="Mean-CVaR Trade-off", risk_aversion=11.0
            )


# =====================================================================
# File extension validation
# =====================================================================


class TestFileValidation:
    """Tests for validate_file_extension."""

    def test_valid_csv_extension(self) -> None:
        ok, info = validate_file_extension("data.csv")
        assert ok is True
        assert info == "csv"

    def test_valid_xlsx_extension(self) -> None:
        ok, info = validate_file_extension("data.xlsx")
        assert ok is True
        assert info == "xlsx"

    def test_valid_xls_extension(self) -> None:
        ok, info = validate_file_extension("data.xls")
        assert ok is True
        assert info == "xls"

    def test_invalid_extension(self) -> None:
        ok, info = validate_file_extension("data.txt")
        assert ok is False
        assert "Unsupported" in info

    def test_empty_filename(self) -> None:
        ok, info = validate_file_extension("")
        assert ok is False

    def test_none_filename(self) -> None:
        ok, info = validate_file_extension(None)  # type: ignore[arg-type]
        assert ok is False

    def test_case_insensitive(self) -> None:
        ok, _ = validate_file_extension("DATA.CSV")
        assert ok is True


# =====================================================================
# Column name sanitization
# =====================================================================


class TestSanitizeColumnNames:
    """Tests for sanitize_column_names."""

    def test_removes_newlines(self) -> None:
        result = sanitize_column_names(["col\n1", "col\r\n2"])
        assert result == ["col 1", "col 2"]

    def test_handles_spaces(self) -> None:
        result = sanitize_column_names(["  spaced  out  "])
        assert result == ["spaced out"]

    def test_handles_tabs(self) -> None:
        result = sanitize_column_names(["col\t1"])
        assert result == ["col 1"]

    def test_truncates_long_names(self) -> None:
        long_name = "A" * 200
        result = sanitize_column_names([long_name])
        assert len(result[0]) <= 100

    def test_empty_string_gets_default(self) -> None:
        result = sanitize_column_names(["", "valid"])
        assert result[0].startswith("Asset_")
        assert result[1] == "valid"

    def test_converts_non_string_to_string(self) -> None:
        result = sanitize_column_names([123, 45.6])
        assert result == ["123", "45.6"]
