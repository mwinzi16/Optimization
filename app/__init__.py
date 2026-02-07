"""Cat Bond Portfolio Optimizer — Flask Application Factory."""

from __future__ import annotations

import uuid
from flask import Flask, g, jsonify, request, render_template
from .config import Settings


def create_app(config: Settings | None = None) -> Flask:
    """Application factory following Flask best practices."""
    app = Flask(__name__)
    
    settings = config or Settings.from_env()
    app.config.from_mapping(
        SECRET_KEY=settings.SECRET_KEY,
        MAX_CONTENT_LENGTH=settings.MAX_UPLOAD_SIZE,
        CORS_ORIGINS=settings.CORS_ORIGINS,
        API_KEY=settings.API_KEY,
        ALLOW_ANONYMOUS=settings.ALLOW_ANONYMOUS,
        RATE_LIMIT_DEFAULT=settings.RATE_LIMIT_DEFAULT,
        REDACT_KEYS=settings.REDACT_KEYS,
        DATA_PATH=settings.DATA_PATH,
    )
    
    # Initialize extensions
    from .extensions import cors, limiter, csrf, talisman
    cors.init_app(app, resources={r"/api/*": {"origins": settings.CORS_ORIGINS}})
    limiter.init_app(app)
    csrf.init_app(app)
    talisman.init_app(
        app,
        force_https=False,  # Allow HTTP in development
        content_security_policy={
            "default-src": "'self'",
            "script-src": (
                "'self' 'unsafe-inline' 'unsafe-eval' "
                "https://cdn.tailwindcss.com https://unpkg.com "
                "https://cdn.plot.ly https://cdn.jsdelivr.net"
            ),
            "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "img-src": "'self' data: blob:",
            "font-src": "'self' https://cdn.jsdelivr.net data:",
            "connect-src": "'self'",
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
        },
    )
    
    # Register blueprints
    from .blueprints.api_v1 import api_v1_bp
    from .blueprints.web import web_bp
    app.register_blueprint(api_v1_bp, url_prefix="/api/v1")
    app.register_blueprint(web_bp)
    
    # Exempt API blueprint from CSRF
    csrf.exempt(api_v1_bp)
    
    # Register error handlers
    from .utils.exceptions import OptimizerError, ErrorCode
    
    @app.errorhandler(OptimizerError)
    def handle_optimizer_error(exc: OptimizerError):
        status_map = {
            ErrorCode.DATA_NOT_LOADED: 500,
            ErrorCode.INVALID_FILE_FORMAT: 400,
            ErrorCode.OPTIMIZATION_FAILED: 422,
            ErrorCode.INVALID_METHOD: 400,
            ErrorCode.INVALID_WEIGHT_RANGE: 400,
            ErrorCode.INTERNAL_ERROR: 500,
        }
        status_code = status_map.get(exc.code, exc.status_code)
        if request.path.startswith("/api/"):
            return jsonify({
                "data": None,
                "meta": {},
                "errors": [{
                    "code": exc.code.value if hasattr(exc.code, "value") else str(exc.code),
                    "message": str(exc),
                    "details": exc.details,
                }],
            }), status_code
        return render_template("errors/500.html", error=exc), status_code

    @app.errorhandler(404)
    def not_found(exc):
        if request.path.startswith("/api/"):
            return jsonify({"data": None, "meta": {}, "errors": [{"code": "NOT_FOUND", "message": "Resource not found", "details": {}}]}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(401)
    def unauthorized(exc):
        if request.path.startswith("/api/"):
            return jsonify({"data": None, "meta": {}, "errors": [{"code": "UNAUTHORIZED", "message": "Invalid or missing API key", "details": {}}]}), 401
        return render_template("errors/500.html", error=exc), 401

    @app.errorhandler(429)
    def rate_limited(exc):
        if request.path.startswith("/api/"):
            return jsonify({"data": None, "meta": {}, "errors": [{"code": "RATE_LIMITED", "message": "Too many requests", "details": {}}]}), 429
        return render_template("errors/500.html", error=exc), 429

    @app.errorhandler(500)
    def internal_error(exc):
        if request.path.startswith("/api/"):
            return jsonify({"data": None, "meta": {}, "errors": [{"code": "INTERNAL_ERROR", "message": "Internal server error", "details": {}}]}), 500
        return render_template("errors/500.html", error=exc), 500
    
    # Request ID middleware
    @app.before_request
    def add_request_id():
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    @app.after_request
    def set_request_id_header(response):
        response.headers["X-Request-ID"] = g.request_id
        return response
    
    # Load initial data
    from .services.data_store import load_data
    with app.app_context():
        load_data(app.config["DATA_PATH"])
    
    return app
