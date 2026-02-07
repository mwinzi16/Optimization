"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
import secrets
import warnings
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    """Application settings from environment variables."""
    
    CORS_ORIGINS: list[str] = field(default_factory=lambda: ["*"])
    API_KEY: str | None = None
    ALLOW_ANONYMOUS: bool = True
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    RATE_LIMIT_DEFAULT: str = "60/minute"
    BIND_HOST: str = "127.0.0.1"
    BIND_PORT: int = 5000
    SECRET_KEY: str = field(default_factory=lambda: secrets.token_hex(32))
    DATA_PATH: str = ""
    REDACT_KEYS: list[str] = field(default_factory=lambda: ["password", "secret", "token", "api_key", "authorization"])
    
    @classmethod
    def from_env(cls) -> Settings:
        """Create settings from environment variables."""
        default_data_path = str(Path(__file__).parent.parent / "data" / "scenario_returns.csv")
        
        cors_raw = os.getenv("CORS_ORIGINS", "*")
        origins = [o.strip().rstrip("/") for o in cors_raw.split(",") if o.strip()]
        
        return cls(
            CORS_ORIGINS=origins,
            API_KEY=os.getenv("API_KEY"),
            ALLOW_ANONYMOUS=os.getenv("ALLOW_ANONYMOUS", "true").lower() in ("true", "1", "yes"),
            MAX_UPLOAD_SIZE=int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024))),
            RATE_LIMIT_DEFAULT=os.getenv("RATE_LIMIT_DEFAULT", "60/minute"),
            BIND_HOST=os.getenv("BIND_HOST", "127.0.0.1"),
            BIND_PORT=int(os.getenv("BIND_PORT", "5000")),
            SECRET_KEY=cls._resolve_secret_key(),
            DATA_PATH=os.getenv("DATA_PATH", default_data_path),
            REDACT_KEYS=os.getenv("REDACT_KEYS", "password,secret,token,api_key,authorization").split(","),
        )

    @staticmethod
    def _resolve_secret_key() -> str:
        """Return SECRET_KEY from env or generate a random one with a warning."""
        key = os.getenv("SECRET_KEY")
        if key:
            return key
        warnings.warn(
            "SECRET_KEY not set — using a randomly generated key. "
            "Sessions and CSRF tokens will not persist across restarts. "
            "Set the SECRET_KEY environment variable for production.",
            stacklevel=3,
        )
        return secrets.token_hex(32)
