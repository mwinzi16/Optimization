"""
API v1 Blueprint — Portfolio Optimizer
=======================================

Flask blueprint providing RESTful endpoints for portfolio optimization,
asset analysis, efficient frontier computation, data upload, and health checks.

Endpoints:
    GET  /api/v1/health              - Health check
    GET  /api/v1/assets              - List available assets with statistics
    POST /api/v1/optimize            - Run portfolio optimization
    GET  /api/v1/efficient-frontier  - Compute efficient frontier
    POST /api/v1/upload              - Upload custom scenario data
    POST /api/v1/reset               - Reset to sample data
    GET  /api/v1/scenarios           - Sample scenario indices

Authors:
    Portfolio Optimizer Team

Version:
    2.0.0
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError as PydanticValidationError

from app.extensions import limiter
from app.schemas.optimization import (
    ValidatedOptimizationRequest,
    sanitize_column_names,
    validate_file_extension,
)
from app.schemas.responses import AssetInfo, EfficientFrontierPoint, OptimizationResponse
from app.services.data_store import data_store, load_data
from app.services.optimizer import CatBondOptimizer
from app.utils.auth import require_api_key
from app.utils.cache import frontier_cache, optimization_cache
from app.utils.exceptions import (
    DataError,
    ErrorCode,
    OptimizationError,
    OptimizerError,
    ValidationError,
)
from app.utils.logger import logger, safe_log_dict

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def envelope(
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None,
    errors: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Wrap response payload in the standard API envelope.

    Args:
        data: Primary response payload.
        meta: Optional metadata (counts, pagination, etc.).
        errors: Optional list of error dicts with code/message/details.

    Returns:
        Dictionary with ``data``, ``meta``, and ``errors`` keys.
    """
    return {
        "data": data,
        "meta": meta or {},
        "errors": errors or [],
    }


# ---------------------------------------------------------------------------
# Error handlers (registered on the blueprint)
# ---------------------------------------------------------------------------


@api_v1_bp.errorhandler(OptimizerError)
def handle_optimizer_error(exc: OptimizerError) -> tuple:
    """Central error handler for all OptimizerError subclasses.

    Maps ``ErrorCode`` to an appropriate HTTP status and returns
    a JSON envelope with structured error details.
    """
    status_map: Dict[ErrorCode, int] = {
        ErrorCode.DATA_NOT_LOADED: 500,
        ErrorCode.INVALID_FILE_FORMAT: 400,
        ErrorCode.OPTIMIZATION_FAILED: 422,
        ErrorCode.INVALID_METHOD: 400,
        ErrorCode.INVALID_WEIGHT_RANGE: 400,
        ErrorCode.INTERNAL_ERROR: 500,
    }
    status_code = status_map.get(exc.code, exc.status_code)
    return (
        jsonify(
            envelope(
                errors=[
                    {
                        "code": exc.code.value
                        if hasattr(exc.code, "value")
                        else str(exc.code),
                        "message": str(exc),
                        "details": exc.details,
                    }
                ]
            )
        ),
        status_code,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@api_v1_bp.route("/health", methods=["GET"])
def health_check() -> tuple:
    """Return application health status.

    No authentication required.

    Returns:
        JSON envelope containing status, version, data_loaded flag,
        and data_shape when data is available.
    """
    df = data_store.returns_df
    return (
        jsonify(
            envelope(
                data={
                    "status": "healthy" if df is not None else "degraded",
                    "version": "2.0.0",
                    "data_loaded": df is not None,
                    "data_shape": (
                        {"scenarios": df.shape[0], "assets": df.shape[1]}
                        if df is not None
                        else None
                    ),
                }
            )
        ),
        200,
    )


@api_v1_bp.route("/assets", methods=["GET"])
def get_assets() -> tuple:
    """List all available assets with summary statistics.

    Computes expected return, no-loss return, expected loss,
    volatility, VaR, and CVaR for each asset in the loaded dataset.

    Raises:
        DataError: If scenario data has not been loaded.

    Returns:
        JSON envelope with a list of ``AssetInfo`` dicts and a count meta.
    """
    returns_df = data_store.returns_df
    if returns_df is None:
        raise DataError("Data not loaded", code=ErrorCode.DATA_NOT_LOADED)

    assets: List[Dict[str, Any]] = []
    for col in returns_df.columns:
        asset_returns: np.ndarray = returns_df[col].values

        no_loss_return = float(np.max(asset_returns))
        mean_return = float(np.mean(asset_returns))
        expected_loss = mean_return - no_loss_return

        var_90 = float(np.percentile(asset_returns, 10))
        var_95 = float(np.percentile(asset_returns, 5))
        var_99 = float(np.percentile(asset_returns, 1))
        cvar_95 = float(
            asset_returns[asset_returns <= var_95].mean()
        )

        assets.append(
            AssetInfo(
                name=col,
                expected_return=mean_return,
                no_loss_return=no_loss_return,
                expected_loss=expected_loss,
                volatility=float(np.std(asset_returns)),
                var_90=var_90,
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
            ).model_dump()
        )

    return jsonify(envelope(data=assets, meta={"count": len(assets)})), 200


@api_v1_bp.route("/optimize", methods=["POST"])
@require_api_key
@limiter.limit("30/minute")
def optimize_portfolio() -> tuple:
    """Run portfolio optimization using the requested method.

    Accepts a JSON body validated against ``ValidatedOptimizationRequest``.
    Supports six optimization strategies and returns optimal weights,
    risk/return metrics, distribution statistics, scenario-level returns,
    and per-asset mean returns.

    Raises:
        DataError: If scenario data has not been loaded.
        ValidationError: If the optimization method is unknown.
        PydanticValidationError: If request body fails validation.

    Returns:
        JSON envelope containing an ``OptimizationResponse`` dict.
    """
    returns_df = data_store.returns_df
    if returns_df is None:
        raise DataError("Data not loaded", code=ErrorCode.DATA_NOT_LOADED)

    # ---- Parse & validate request body ----
    body = request.get_json(silent=True)
    if body is None:
        return (
            jsonify(
                envelope(
                    errors=[
                        {
                            "code": "ERR_3001",
                            "message": "Request body must be valid JSON",
                            "details": {},
                        }
                    ]
                )
            ),
            400,
        )

    try:
        req = ValidatedOptimizationRequest(**body)
    except PydanticValidationError as exc:
        return (
            jsonify(
                envelope(
                    errors=[
                        {
                            "code": "ERR_3001",
                            "message": "Validation error",
                            "details": exc.errors(),
                        }
                    ]
                )
            ),
            422,
        )

    # ---- Create a LOCAL optimizer (does NOT mutate global state) ----
    opt = data_store.get_optimizer(req.risk_free_rate)

    # ---- Method dispatch ----
    method = (
        req.method.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
    )

    if method in ("maximum_sharpe_ratio", "max_sharpe"):
        result = opt.optimize_max_sharpe(req.min_weight, req.max_weight)
    elif method in ("minimum_variance", "min_variance"):
        result = opt.optimize_min_variance(req.min_weight, req.max_weight)
    elif method in ("minimum_cvar", "min_cvar"):
        result = opt.optimize_min_cvar(
            req.cvar_alpha, req.min_weight, req.max_weight
        )
    elif method in ("mean-cvar_trade-off", "mean_cvar"):
        result = opt.optimize_mean_cvar(
            req.cvar_alpha,
            req.risk_aversion,
            req.min_weight,
            req.max_weight,
        )
    elif method in ("maximum_return_constrained", "max_return"):
        if req.constraint_type == "volatility":
            result = opt.optimize_max_return(
                max_volatility=req.max_volatility or 0.15,
                min_weight=req.min_weight,
                max_weight=req.max_weight,
            )
        else:
            result = opt.optimize_max_return(
                max_cvar=req.max_cvar or 0.25,
                alpha=req.cvar_constraint_alpha,
                min_weight=req.min_weight,
                max_weight=req.max_weight,
            )
    elif method in ("exponential_utility_cara", "exponential_utility"):
        result = opt.optimize_exponential_utility(
            req.exp_risk_aversion, req.min_weight, req.max_weight
        )
    else:
        raise ValidationError(
            f"Unknown optimization method: {req.method}",
            code=ErrorCode.INVALID_METHOD,
        )

    # ---- Compute response data ----
    weights: np.ndarray = result["weights"]
    metrics = opt._compute_portfolio_metrics(weights)
    dist_stats = opt._compute_distribution_stats(weights)

    original_portfolio_returns: np.ndarray = (
        opt.original_returns_matrix @ weights
    )
    portfolio_returns: List[float] = original_portfolio_returns.tolist()

    # Best scenario (highest portfolio return)
    best_scenario_idx = int(np.argmax(original_portfolio_returns))
    best_scenario_asset_returns = opt.original_returns_matrix[
        best_scenario_idx, :
    ]
    best_scenario_returns: Dict[str, float] = {
        asset: float(r)
        for asset, r in zip(opt.assets, best_scenario_asset_returns)
    }

    # VaR scenario indices
    sorted_indices = np.argsort(original_portfolio_returns)
    n_scenarios = len(original_portfolio_returns)
    var90_idx = sorted_indices[int(n_scenarios * 0.10)]
    var95_idx = sorted_indices[int(n_scenarios * 0.05)]
    var99_idx = sorted_indices[int(n_scenarios * 0.01)]

    var90_scenario_returns: Dict[str, float] = {
        asset: float(r)
        for asset, r in zip(
            opt.assets, opt.original_returns_matrix[var90_idx, :]
        )
    }
    var95_scenario_returns: Dict[str, float] = {
        asset: float(r)
        for asset, r in zip(
            opt.assets, opt.original_returns_matrix[var95_idx, :]
        )
    }
    var99_scenario_returns: Dict[str, float] = {
        asset: float(r)
        for asset, r in zip(
            opt.assets, opt.original_returns_matrix[var99_idx, :]
        )
    }

    # Mean returns per asset
    asset_mean_returns: Dict[str, float] = {
        asset: float(r)
        for asset, r in zip(
            opt.assets, opt.original_returns_matrix.mean(axis=0)
        )
    }

    response_dict = OptimizationResponse(
        status=result["status"],
        method=result["method"],
        weights={
            asset: float(w) for asset, w in zip(opt.assets, weights)
        },
        metrics=metrics,
        portfolio_returns=portfolio_returns,
        distribution_stats=dist_stats,
        best_scenario_returns=best_scenario_returns,
        var90_scenario_returns=var90_scenario_returns,
        var95_scenario_returns=var95_scenario_returns,
        var99_scenario_returns=var99_scenario_returns,
        asset_mean_returns=asset_mean_returns,
    ).model_dump()

    return jsonify(envelope(data=response_dict)), 200


@api_v1_bp.route("/efficient-frontier", methods=["GET"])
def get_efficient_frontier() -> tuple:
    """Compute the mean-variance efficient frontier.

    Query Parameters:
        min_weight: Minimum allocation per asset (default 0.0).
        max_weight: Maximum allocation per asset (default 1.0).
        n_points: Number of frontier points (default 20, min 5, max 100).
        risk_free_rate: Risk-free rate for Sharpe calculation (default 0.0).

    Raises:
        DataError: If scenario data has not been loaded.

    Returns:
        JSON envelope with a list of ``EfficientFrontierPoint`` dicts.
    """
    if data_store.returns_df is None:
        raise DataError("Data not loaded", code=ErrorCode.DATA_NOT_LOADED)

    # ---- Parse query parameters with defaults and bounds ----
    try:
        min_weight = float(request.args.get("min_weight", 0.0))
        max_weight = float(request.args.get("max_weight", 1.0))
        n_points = int(request.args.get("n_points", 20))
        risk_free_rate = float(request.args.get("risk_free_rate", 0.0))
    except (ValueError, TypeError) as exc:
        return (
            jsonify(
                envelope(
                    errors=[
                        {
                            "code": "ERR_3001",
                            "message": f"Invalid query parameter: {exc}",
                            "details": {},
                        }
                    ]
                )
            ),
            400,
        )

    # Clamp n_points to [5, 100]
    n_points = max(5, min(n_points, 100))

    frontier_optimizer = data_store.get_optimizer(risk_free_rate)
    frontier: List[Dict[str, float]] = frontier_optimizer.efficient_frontier(
        n_points, min_weight, max_weight
    )

    return (
        jsonify(envelope(data=frontier, meta={"n_points": len(frontier)})),
        200,
    )


@api_v1_bp.route("/upload", methods=["POST"])
@require_api_key
def upload_data() -> tuple:
    """Upload a CSV or Excel file with scenario returns.

    Expected format: first column is the scenario index; remaining
    columns are asset return series. Validates file size, extension,
    content type, formula injection, and minimum asset/scenario counts.

    Raises:
        DataError: On invalid file format, empty data, or insufficient
            assets/scenarios.

    Returns:
        JSON envelope with upload status, asset count, scenario count,
        and asset names.
    """
    file = request.files.get("file")
    if file is None:
        return (
            jsonify(
                envelope(
                    errors=[
                        {
                            "code": ErrorCode.INVALID_FILE_FORMAT.value,
                            "message": "No file provided",
                            "details": {},
                        }
                    ]
                )
            ),
            400,
        )

    try:
        contents: bytes = file.read()
        redact_keys = current_app.config.get("REDACT_KEYS", [])
        safe_log_dict(
            logger,
            {"filename": file.filename, "size": len(contents)},
            redact_keys=redact_keys,
        )

        # ---- Enforce upload size limit ----
        max_upload_size: int = current_app.config.get(
            "MAX_UPLOAD_SIZE", 10 * 1024 * 1024
        )
        if len(contents) > max_upload_size:
            return (
                jsonify(
                    envelope(
                        errors=[
                            {
                                "code": ErrorCode.INVALID_FILE_FORMAT.value,
                                "message": (
                                    f"File too large. Max size = {max_upload_size} bytes"
                                ),
                                "details": {},
                            }
                        ]
                    )
                ),
                413,
            )

        # ---- Validate extension ----
        ok, info = validate_file_extension(file.filename or "")
        if not ok:
            raise DataError(info, code=ErrorCode.INVALID_FILE_FORMAT)

        # ---- Validate content type ----
        allowed_content_types = {
            "text/csv",
            "application/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "application/octet-stream",
        }
        if (
            file.content_type
            and file.content_type not in allowed_content_types
        ):
            return (
                jsonify(
                    envelope(
                        errors=[
                            {
                                "code": ErrorCode.INVALID_FILE_FORMAT.value,
                                "message": (
                                    f"Unsupported content type: {file.content_type}"
                                ),
                                "details": {},
                            }
                        ]
                    )
                ),
                400,
            )

        # ---- Read into DataFrame ----
        filename_lower = (file.filename or "").lower()
        if filename_lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents), index_col=0)
        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents), index_col=0)
        else:
            raise DataError(
                "Unsupported file format. Use CSV or Excel.",
                code=ErrorCode.INVALID_FILE_FORMAT,
            )

        # ---- Sanitize column names ----
        df.columns = sanitize_column_names(df.columns.tolist())

        # ---- Validate: non-empty ----
        if df.empty:
            raise DataError("File is empty", code=ErrorCode.FILE_EMPTY)

        # ---- Check for formula injection in object columns ----
        object_cols = df.select_dtypes(include=["object"]).columns.tolist()
        if object_cols:
            for col in object_cols:
                series = df[col].astype(str).fillna("")
                if series.str.match(r"^[=+\-@]").any():
                    raise DataError(
                        "File contains potentially dangerous formula cells. "
                        "Remove leading =, +, - or @ from values.",
                        code=ErrorCode.INVALID_FILE_FORMAT,
                    )

        # ---- Convert to numeric ----
        df = df.apply(pd.to_numeric, errors="coerce")
        df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")

        # ---- Validate minimum dimensions ----
        if df.shape[1] < 2:
            raise DataError(
                "Need at least 2 assets",
                code=ErrorCode.INSUFFICIENT_ASSETS,
            )

        if df.shape[0] < 100:
            raise DataError(
                "Need at least 100 scenarios",
                code=ErrorCode.INSUFFICIENT_SCENARIOS,
            )

        # ---- Persist ----
        data_store.update(df, risk_free_rate=0.0)

        return (
            jsonify(
                envelope(
                    data={
                        "status": "success",
                        "n_assets": df.shape[1],
                        "n_scenarios": df.shape[0],
                        "asset_names": list(df.columns),
                    }
                )
            ),
            200,
        )

    except OptimizerError:
        raise
    except Exception:
        logger.exception("File upload processing error")
        raise DataError(
            "Failed to process uploaded file",
            code=ErrorCode.INVALID_FILE_FORMAT,
        )


@api_v1_bp.route("/reset", methods=["POST"])
@require_api_key
def reset_data() -> tuple:
    """Reset the in-memory dataset to the default sample data.

    Reads ``DATA_PATH`` from the application config and reloads data.

    Raises:
        OptimizerError: If the sample data file cannot be loaded.

    Returns:
        JSON envelope with status and confirmation message.
    """
    try:
        data_path: str = current_app.config.get("DATA_PATH", "")
        load_data(data_path)
        logger.info("Data reset to sample data via API reset endpoint")
        return (
            jsonify(
                envelope(
                    data={
                        "status": "success",
                        "message": "Reset to sample data",
                    }
                )
            ),
            200,
        )
    except Exception:
        logger.exception("Failed to reset data")
        raise OptimizerError(
            "Internal server error", code=ErrorCode.INTERNAL_ERROR
        )


@api_v1_bp.route("/scenarios", methods=["GET"])
def get_scenarios() -> tuple:
    """Return a sample of scenario indices for visualization.

    Query Parameters:
        sample_size: Number of evenly spaced indices to return
            (default 1000).

    Raises:
        DataError: If scenario data has not been loaded.

    Returns:
        JSON envelope with sampled scenario indices, total scenario
        count, and asset names.
    """
    returns_df = data_store.returns_df
    if returns_df is None:
        raise DataError("Data not loaded", code=ErrorCode.DATA_NOT_LOADED)

    try:
        sample_size = int(request.args.get("sample_size", 1000))
    except (ValueError, TypeError):
        sample_size = 1000

    n = len(returns_df)
    indices = np.linspace(0, n - 1, min(sample_size, n), dtype=int)

    return (
        jsonify(
            envelope(
                data={
                    "scenarios": indices.tolist(),
                    "n_total": n,
                    "assets": returns_df.columns.tolist(),
                }
            )
        ),
        200,
    )
