"""Simple in-memory rate limiting middleware.

This implementation is intentionally lightweight and should be replaced with
an external store (Redis) for multi-worker deployments.
"""

from __future__ import annotations

import time
from typing import Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP fixed-window counter.

    Configurable via middleware init params. Not suitable for clustered apps
    (use Redis for global counters instead).
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        # Structure: {ip: (window_start_ts, count)}
        self._counters: Dict[str, tuple[float, int]] = {}

    async def dispatch(self, request: Request, call_next):
        client = request.client.host if request.client else "unknown"
        now = time.time()

        window_start, count = self._counters.get(client, (0.0, 0))
        if now - window_start >= self.window:
            # reset window
            window_start = now
            count = 0

        count += 1
        self._counters[client] = (window_start, count)

        if count > self.max_requests:
            return JSONResponse({"detail": "Too many requests"}, status_code=429)

        response = await call_next(request)
        return response
