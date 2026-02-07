"""Web blueprint — Flask frontend for the portfolio optimizer.

Serves the standalone web application (HTMX-driven) that replaces the
Streamlit prototype.  All routes are synchronous.  HTMX endpoints return
HTML partials; full-page requests return complete Jinja2 templates.
"""

from __future__ import annotations

import io
from typing import Any, Dict

import numpy as np
import pandas as pd
from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from app.schemas.optimization import sanitize_column_names, validate_file_extension
from app.services.data_store import data_store, load_data
from app.services.optimizer import CatBondOptimizer
from app.services.stats import compute_additional_stats
from app.utils.charts import (
    create_cvar_frontier_chart,
    create_efficient_frontier_chart,
    create_probability_chart,
    create_return_distribution_chart,
    create_scenario_heatmap,
    create_weights_chart,
)
from app.utils.logger import logger

web_bp = Blueprint(
    "web",
    __name__,
    template_folder="../templates",
    static_folder="../static",
)

# ---------------------------------------------------------------------------
# Method descriptions (mirrors the Streamlit app.py copy)
# ---------------------------------------------------------------------------

METHOD_DESCRIPTIONS: Dict[str, str] = {
    "Maximum Sharpe Ratio": (
        "Maximises the Sharpe ratio (excess return per unit of volatility). "
        "Best when you want the highest risk-adjusted return."
    ),
    "Minimum Variance": (
        "Minimises portfolio variance (volatility). "
        "Best for the most conservative allocation."
    ),
    "Minimum CVaR": (
        "Minimises Conditional Value-at-Risk (expected loss in the worst tail). "
        "Focuses on reducing extreme downside."
    ),
    "Mean-CVaR Trade-off": (
        "Balances expected return against CVaR via a risk-aversion parameter. "
        "Higher risk aversion penalises tail risk more."
    ),
    "Maximum Return (Constrained)": (
        "Maximises expected return subject to a volatility or CVaR constraint. "
        "Useful when you have a specific risk budget."
    ),
    "Exponential Utility (CARA)": (
        "Maximises expected exponential (CARA) utility. "
        "Captures non-linear risk preferences."
    ),
}

VALID_METHODS = list(METHOD_DESCRIPTIONS.keys())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@web_bp.route("/")
def index() -> str:
    """Render the main application page.

    Passes dataset metadata (loaded flag, counts, asset names) to the
    ``index.html`` template.

    Returns:
        Rendered ``index.html`` page.
    """
    df = data_store.returns_df
    data_loaded = df is not None

    return render_template(
        "index.html",
        data_loaded=data_loaded,
        n_scenarios=df.shape[0] if data_loaded else 0,
        n_assets=df.shape[1] if data_loaded else 0,
        asset_names=list(df.columns) if data_loaded else [],
        methods=VALID_METHODS,
        method_descriptions=METHOD_DESCRIPTIONS,
    )


@web_bp.route("/optimize", methods=["POST"])
def optimize() -> str:
    """Run portfolio optimisation from form data (HTMX endpoint).

    Reads all optimisation parameters from ``request.form``, dispatches
    to the appropriate ``CatBondOptimizer`` method, computes metrics and
    charts, then returns the ``partials/optimization_results.html``
    partial for HTMX swap.

    Returns:
        Rendered results partial with all computed data and chart JSON.
    """
    try:
        # ---- Parse form parameters ----
        method = request.form.get("method", "Maximum Sharpe Ratio")
        risk_free_rate = float(request.form.get("risk_free_rate", "4.0")) / 100
        min_weight = float(request.form.get("min_weight", "0.0")) / 100
        max_weight = float(request.form.get("max_weight", "100.0")) / 100
        cvar_alpha_pct = int(request.form.get("cvar_alpha", "95"))
        alpha = (100 - cvar_alpha_pct) / 100
        risk_aversion = float(request.form.get("risk_aversion", "1.0"))
        constraint_type = request.form.get("constraint_type", "volatility")
        max_volatility = float(request.form.get("max_volatility", "15.0")) / 100
        max_cvar = float(request.form.get("max_cvar", "25.0")) / 100
        exp_risk_aversion = float(request.form.get("exp_risk_aversion", "0.5"))

        # ---- Obtain optimizer ----
        opt = data_store.get_optimizer(risk_free_rate)
        returns_df = data_store.returns_df

        # ---- Method dispatch ----
        norm = method.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")

        if norm in ("maximum_sharpe_ratio", "max_sharpe"):
            result = opt.optimize_max_sharpe(min_weight, max_weight)
        elif norm in ("minimum_variance", "min_variance"):
            result = opt.optimize_min_variance(min_weight, max_weight)
        elif norm in ("minimum_cvar", "min_cvar"):
            result = opt.optimize_min_cvar(alpha, min_weight, max_weight)
        elif norm in ("mean_cvar_trade_off", "mean_cvar"):
            result = opt.optimize_mean_cvar(alpha, risk_aversion, min_weight, max_weight)
        elif norm in ("maximum_return_constrained", "max_return"):
            if constraint_type == "volatility":
                result = opt.optimize_max_return(
                    max_volatility=max_volatility,
                    min_weight=min_weight,
                    max_weight=max_weight,
                )
            else:
                result = opt.optimize_max_return(
                    max_cvar=max_cvar,
                    alpha=alpha,
                    min_weight=min_weight,
                    max_weight=max_weight,
                )
        elif norm in ("exponential_utility_cara", "exponential_utility"):
            result = opt.optimize_exponential_utility(
                exp_risk_aversion, min_weight, max_weight
            )
        else:
            return render_template(
                "partials/toast.html",
                message=f"Unknown optimisation method: {method}",
                level="error",
            )

        # ---- Compute metrics ----
        weights: np.ndarray = result["weights"]
        weights_dict: Dict[str, float] = {
            asset: float(w) for asset, w in zip(opt.assets, weights)
        }
        metrics = opt._compute_portfolio_metrics(weights)
        distribution_stats = opt._compute_distribution_stats(weights)
        portfolio_returns = opt.original_returns_matrix @ weights
        additional_stats = compute_additional_stats(portfolio_returns, rf=risk_free_rate)

        # Benchmark (equal-weight)
        benchmark = opt.get_equal_weight_metrics()

        # Efficient frontier
        frontier = opt.efficient_frontier(n_points=20, min_weight=min_weight, max_weight=max_weight)

        # ---- Build charts ----
        chart_distribution = create_return_distribution_chart(
            portfolio_returns,
            metrics["var_95"],
            metrics["cvar_95"],
            metrics["var_99"],
        ).to_json()

        chart_weights = create_weights_chart(weights_dict).to_json()

        chart_frontier = create_efficient_frontier_chart(
            frontier,
            {"expected_return": metrics["expected_return"], "volatility": metrics["volatility"]},
            {"expected_return": benchmark["expected_return"], "volatility": benchmark["volatility"]},
        ).to_json()

        chart_cvar_frontier = create_cvar_frontier_chart(
            frontier,
            {"expected_return": metrics["expected_return"], "cvar_95": metrics["cvar_95"]},
        ).to_json()

        chart_heatmap = create_scenario_heatmap(
            returns_df,  # type: ignore[arg-type]
            weights_dict,
        ).to_json()

        chart_probability = create_probability_chart(portfolio_returns).to_json()

        return render_template(
            "partials/optimization_results.html",
            status=result["status"],
            method=result["method"],
            method_display=method,
            weights=weights_dict,
            metrics=metrics,
            distribution_stats=distribution_stats,
            additional_stats=additional_stats,
            benchmark=benchmark,
            frontier=frontier,
            chart_distribution=chart_distribution,
            chart_weights=chart_weights,
            chart_frontier=chart_frontier,
            chart_cvar_frontier=chart_cvar_frontier,
            chart_heatmap=chart_heatmap,
            chart_probability=chart_probability,
        )

    except ValueError as exc:
        logger.warning("Optimisation form error: %s", exc)
        return render_template(
            "partials/toast.html",
            message=f"Invalid input: {exc}",
            level="error",
        )
    except Exception:
        logger.exception("Optimisation failed")
        return render_template(
            "partials/toast.html",
            message="Optimisation failed. Please check your parameters and try again.",
            level="error",
        )


@web_bp.route("/upload", methods=["POST"])
def upload() -> str:
    """Upload a CSV file with scenario returns (HTMX endpoint).

    Validates extension, size, content type, formula injection, minimum
    column/row counts, then persists to the data store.

    Returns:
        ``partials/data_status.html`` on success or
        ``partials/toast.html`` with error on failure.
    """
    try:
        file = request.files.get("file")
        if file is None:
            return render_template(
                "partials/toast.html",
                message="No file provided.",
                level="error",
            )

        contents: bytes = file.read()

        # ---- Size limit ----
        max_upload_size: int = current_app.config.get(
            "MAX_UPLOAD_SIZE", 10 * 1024 * 1024
        )
        if len(contents) > max_upload_size:
            return render_template(
                "partials/toast.html",
                message=f"File too large. Maximum size is {max_upload_size // (1024 * 1024)} MB.",
                level="error",
            )

        # ---- Extension ----
        ok, info = validate_file_extension(file.filename or "")
        if not ok:
            return render_template(
                "partials/toast.html", message=info, level="error"
            )

        # ---- Content type ----
        allowed_content_types = {
            "text/csv",
            "application/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "application/octet-stream",
        }
        if file.content_type and file.content_type not in allowed_content_types:
            return render_template(
                "partials/toast.html",
                message=f"Unsupported content type: {file.content_type}",
                level="error",
            )

        # ---- Read into DataFrame ----
        filename_lower = (file.filename or "").lower()
        if filename_lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents), index_col=0)
        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents), index_col=0)
        else:
            return render_template(
                "partials/toast.html",
                message="Unsupported file format. Use CSV or Excel.",
                level="error",
            )

        # ---- Sanitize column names ----
        df.columns = sanitize_column_names(df.columns.tolist())

        # ---- Validate non-empty ----
        if df.empty:
            return render_template(
                "partials/toast.html", message="File is empty.", level="error"
            )

        # ---- Formula injection check ----
        object_cols = df.select_dtypes(include=["object"]).columns.tolist()
        if object_cols:
            for col in object_cols:
                series = df[col].astype(str).fillna("")
                if series.str.match(r"^[=+\-@]").any():
                    return render_template(
                        "partials/toast.html",
                        message="File contains potentially dangerous formula cells.",
                        level="error",
                    )

        # ---- Numeric conversion ----
        df = df.apply(pd.to_numeric, errors="coerce")
        df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")

        # ---- Minimum dimensions ----
        if df.shape[1] < 2:
            return render_template(
                "partials/toast.html",
                message="Need at least 2 asset columns.",
                level="error",
            )
        if df.shape[0] < 100:
            return render_template(
                "partials/toast.html",
                message="Need at least 100 scenarios (rows).",
                level="error",
            )

        # ---- Persist ----
        data_store.update(df, risk_free_rate=0.0)
        logger.info(
            "User uploaded data: %d scenarios × %d assets",
            df.shape[0],
            df.shape[1],
        )

        return render_template(
            "partials/data_status.html",
            data_loaded=True,
            n_scenarios=df.shape[0],
            n_assets=df.shape[1],
            asset_names=list(df.columns),
        )

    except Exception:
        logger.exception("Upload processing error")
        return render_template(
            "partials/toast.html",
            message="Failed to process file. Please check the format and try again.",
            level="error",
        )


@web_bp.route("/reset", methods=["POST"])
def reset() -> str:
    """Reset the dataset to the bundled sample data (HTMX endpoint).

    Re-reads the CSV at ``DATA_PATH`` and returns an updated
    ``partials/data_status.html`` partial.

    Returns:
        Rendered data-status partial.
    """
    try:
        data_path: str = current_app.config.get("DATA_PATH", "")
        load_data(data_path)
        logger.info("Data reset to sample data via web UI")

        df = data_store.returns_df
        return render_template(
            "partials/data_status.html",
            data_loaded=df is not None,
            n_scenarios=df.shape[0] if df is not None else 0,
            n_assets=df.shape[1] if df is not None else 0,
            asset_names=list(df.columns) if df is not None else [],
        )
    except Exception:
        logger.exception("Reset failed")
        return render_template(
            "partials/toast.html",
            message="Reset failed. Please try again later.",
            level="error",
        )


@web_bp.route("/method-params/<method>", methods=["GET"])
def method_params(method: str) -> str:
    """Return method-specific form controls (HTMX endpoint).

    Args:
        method: The optimisation method name (URL-encoded).

    Returns:
        Rendered ``partials/method_params.html`` partial with the
        appropriate context variables for the selected method.
    """
    show_cvar_alpha = method in (
        "Minimum CVaR",
        "Mean-CVaR Trade-off",
        "Maximum Return (Constrained)",
    )
    show_risk_aversion = method == "Mean-CVaR Trade-off"
    show_constraint_type = method == "Maximum Return (Constrained)"
    show_exp_risk_aversion = method == "Exponential Utility (CARA)"

    return render_template(
        "partials/method_params.html",
        method=method,
        description=METHOD_DESCRIPTIONS.get(method, ""),
        show_cvar_alpha=show_cvar_alpha,
        show_risk_aversion=show_risk_aversion,
        show_constraint_type=show_constraint_type,
        show_exp_risk_aversion=show_exp_risk_aversion,
    )
