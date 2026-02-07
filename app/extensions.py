"""Flask extension instances initialized here, bound in create_app()."""

from __future__ import annotations

from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

cors = CORS()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()
talisman = Talisman()
