"""
Configuration helpers for the API.

Read runtime configuration from environment variables with sensible
defaults for local development. Keeps secrets out of source code.
"""
import os
from typing import List


def _split_origins(value: str) -> List[str]:
    if not value:
        return ["http://localhost:3000"]
    return [o.strip() for o in value.split(",") if o.strip()]


# CORS
CORS_ORIGINS = _split_origins(os.environ.get("CORS_ORIGINS", "http://localhost:3000"))

# Simple API key (for small deployments). If not set, API key validation fails
# unless `ALLOW_ANONYMOUS` is set to a truthy value (dev convenience only).
API_KEY = os.environ.get("API_KEY")
ALLOW_ANONYMOUS = os.environ.get("ALLOW_ANONYMOUS", "false").lower() in ("1", "true", "yes")

# Upload limits (bytes)
MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", 5 * 1024 * 1024))  # default 5 MB

# Uvicorn binding defaults
BIND_HOST = os.environ.get("BIND_HOST", "127.0.0.1")
BIND_PORT = int(os.environ.get("BIND_PORT", "8000"))

# Rate limiting defaults
RATE_LIMIT_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "60"))  # requests
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))  # seconds

# Keys to redact when logging dict-like data
REDACT_KEYS = [k.strip().lower() for k in os.environ.get("REDACT_KEYS", "password,passwd,secret,api_key,authorization").split(",")]


__all__ = [
    "CORS_ORIGINS",
    "API_KEY",
    "ALLOW_ANONYMOUS",
    "MAX_UPLOAD_SIZE",
    "BIND_HOST",
    "BIND_PORT",
]
