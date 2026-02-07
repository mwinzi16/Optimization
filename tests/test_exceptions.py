"""
Unit tests for the custom exception hierarchy and error codes.
"""

from __future__ import annotations

import pytest

from backend.utils.exceptions import (
    DataError,
    ErrorCode,
    OptimizationError,
    OptimizerError,
    ValidationError,
)


# =====================================================================
# OptimizerError (base)
# =====================================================================


def test_optimizer_error_has_code() -> None:
    err = OptimizerError("boom", code=ErrorCode.INTERNAL_ERROR)
    assert err.code == ErrorCode.INTERNAL_ERROR
    assert err.message == "boom"
    assert err.status_code == 500


def test_optimizer_error_default_details_empty() -> None:
    err = OptimizerError("msg")
    assert err.details == {}


def test_optimizer_error_to_dict_format() -> None:
    err = OptimizerError(
        "bad thing", code=ErrorCode.NUMERICAL_ERROR, details={"info": 1}
    )
    d = err.to_dict()
    assert d["error"] is True
    assert d["code"] == "ERR_2004"
    assert d["message"] == "bad thing"
    assert d["details"] == {"info": 1}


# =====================================================================
# DataError
# =====================================================================


def test_data_error_inherits_from_optimizer_error() -> None:
    err = DataError("no data")
    assert isinstance(err, OptimizerError)
    assert err.status_code == 400


def test_data_error_default_code() -> None:
    err = DataError("missing")
    assert err.code == ErrorCode.DATA_NOT_LOADED


def test_data_error_custom_code() -> None:
    err = DataError("empty", code=ErrorCode.FILE_EMPTY)
    assert err.code == ErrorCode.FILE_EMPTY


# =====================================================================
# ValidationError
# =====================================================================


def test_validation_error_inherits() -> None:
    err = ValidationError("invalid input")
    assert isinstance(err, OptimizerError)
    assert err.status_code == 422


def test_validation_error_default_code() -> None:
    err = ValidationError("bad weight")
    assert err.code == ErrorCode.INVALID_WEIGHT_RANGE


# =====================================================================
# OptimizationError
# =====================================================================


def test_optimization_error_inherits() -> None:
    err = OptimizationError("solver failed")
    assert isinstance(err, OptimizerError)
    assert err.status_code == 500


def test_optimization_error_default_code() -> None:
    err = OptimizationError("oops")
    assert err.code == ErrorCode.OPTIMIZATION_FAILED


# =====================================================================
# ErrorCode enum
# =====================================================================


def test_error_code_enum_values() -> None:
    assert ErrorCode.DATA_NOT_LOADED.value == "ERR_1001"
    assert ErrorCode.INVALID_FILE_FORMAT.value == "ERR_1002"
    assert ErrorCode.FILE_EMPTY.value == "ERR_1003"
    assert ErrorCode.INSUFFICIENT_ASSETS.value == "ERR_1004"
    assert ErrorCode.OPTIMIZATION_FAILED.value == "ERR_2001"
    assert ErrorCode.INVALID_METHOD.value == "ERR_2002"
    assert ErrorCode.INTERNAL_ERROR.value == "ERR_5001"


def test_error_code_is_string_enum() -> None:
    assert isinstance(ErrorCode.DATA_NOT_LOADED, str)
    assert ErrorCode.DATA_NOT_LOADED == "ERR_1001"


def test_all_error_codes_have_err_prefix() -> None:
    for code in ErrorCode:
        assert code.value.startswith("ERR_")
