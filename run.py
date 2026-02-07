"""Flask application entry point.

Exposes ``app`` at module level for gunicorn::

    gunicorn run:app --bind 0.0.0.0:5000

Also supports direct execution::

    python run.py
"""

from __future__ import annotations

from app import create_app
from app.config import Settings

settings: Settings = Settings.from_env()
app = create_app(settings)


if __name__ == "__main__":
    app.run(
        host=settings.BIND_HOST,
        port=settings.BIND_PORT,
        debug=True,
    )
