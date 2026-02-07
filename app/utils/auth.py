"""API key authentication decorator for protected endpoints."""

from __future__ import annotations

import hmac
from functools import wraps
from typing import Callable

from flask import abort, current_app, request


def require_api_key(f: Callable) -> Callable:
    """Decorator to protect endpoints with API key authentication.
    
    Reads X-API-Key header and compares via hmac.compare_digest.
    Skips check if ALLOW_ANONYMOUS is True.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_app.config.get("ALLOW_ANONYMOUS", False):
            return f(*args, **kwargs)
        
        api_key = current_app.config.get("API_KEY")
        if not api_key:
            abort(500, description="Server authentication configuration error")
        
        provided = request.headers.get("X-API-Key", "")
        if not provided or not hmac.compare_digest(provided, api_key):
            abort(401, description="Invalid or missing API key")
        
        return f(*args, **kwargs)
    return decorated
