# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- User authentication (OAuth2)
- Portfolio save/load functionality
- PDF report generation
- Real-time WebSocket updates
- Monte Carlo simulation
- Black-Litterman model support

---

## [3.0.0] - 2026-02-14

### Changed — BREAKING
- **Migrated from FastAPI to Flask** — complete rewrite of backend using Flask application factory pattern with Blueprints
- **Unified Web UI** — replaced React SPA and Streamlit app with Flask/Jinja2 templates + HTMX + Tailwind CSS + Plotly.js
- **Single deployment target** — consolidated 3 Docker services (backend, frontend, streamlit) into one Flask service on port 5000
- **WSGI server** — switched from uvicorn (ASGI) to gunicorn (WSGI)

### Added
- Flask application factory (`create_app()`) with dependency injection via `Settings` dataclass
- API v1 Blueprint (`/api/v1/`) preserving all 7 REST endpoints with identical contracts
- Web Blueprint (`/`) with server-rendered HTMX-driven UI
- CSRF protection via Flask-WTF (forms) with API blueprint exemption
- Security headers via Flask-Talisman
- Rate limiting via Flask-Limiter (replaces custom Starlette middleware)
- 6 Plotly chart generators (histogram, donut, frontier, CVaR frontier, heatmap, CDF)
- HTMX-powered partial rendering for method parameters, optimization results, data status, toasts
- KaTeX math formula rendering for optimization method documentation
- `run.py` entry point for both direct and gunicorn execution
- Comprehensive pytest test suite (192+ tests) with pytest-flask integration
- `conftest.py` with session-scoped fixtures for Flask app, test client, and synthetic data

### Removed
- FastAPI dependency and all async/ASGI code
- React frontend (TypeScript, Vite, Recharts, npm ecosystem)
- Streamlit standalone app
- uvicorn ASGI server
- `requirements-streamlit.txt` (no longer needed, kept as deprecated)

### Migration Notes
- API contracts unchanged — all 7 endpoints return identical JSON envelopes
- Port changed from 8000 to 5000
- Docker Compose reduced from 3 services to 1
- Frontend now server-rendered (no separate build step)

---

## [2.1.0] - 2026-02-07

### Fixed — CRITICAL
- **Max Sharpe transformation method** — corrected convex reformulation that produced sub-optimal portfolios
- **Efficient frontier return space** — frontier now spans the full feasible return range instead of a truncated subset
- **Thread-safe data store** — replaced mutable global state with a lock-guarded store to prevent data races under concurrent requests
- **API key timing attack** — switched to `secrets.compare_digest` for constant-time API key comparison

### Fixed — HIGH
- **Custom exception hierarchy** — introduced `AppError` base with typed sub-classes; central error handler returns structured JSON
- **LRU caching with TTL** — optimization and frontier results are cached with configurable TTL; cache invalidated on data upload/reset
- **Validation wiring** — all request bodies are validated through Pydantic models before reaching business logic
- **Pinned dependencies** — `requirements.txt` now uses lower+upper bounds (e.g. `>=X,<Y`) for reproducible installs
- **Correlation ID middleware** — every request/response carries a unique `X-Correlation-ID` header for tracing
- **Exponential utility overflow** — clamped exponent range to prevent `np.exp` overflow in CARA optimization

### Fixed — MEDIUM
- **API versioning** — all endpoints moved under `/api/v1/` prefix via `APIRouter(prefix="/api/v1")`
- **Response envelope** — every JSON response wrapped in `{"data": …, "meta": …, "errors": …}` structure
- **Content-type validation** — upload endpoint rejects non-CSV/Excel MIME types before processing

### Added
- **React frontend reconstruction** — full rewrite with TypeScript, Tailwind CSS, Recharts, accessibility (ARIA), keyboard shortcuts
- **Drag-and-drop file upload** — CSV and Excel support with client-side validation and progress indicator
- **Methodology explanations** — in-app tooltips describing each optimization method and risk metric
- **Docker deployment** — production-ready Dockerfiles (backend, frontend, Streamlit) and `docker-compose.yml`
- **`requirements-dev.txt`** — pytest, ruff, black, mypy, bandit, safety
- **`requirements-streamlit.txt`** — streamlit + plotly for standalone app

### Added

#### Backend
- **Structured logging** with request timing and correlation IDs
- **Custom exceptions** with error codes for better error handling
- **Pydantic validation** for all request models
- **LRU caching** with TTL for optimization and frontier results
- **Utils package** (`backend/utils/`) with modular utilities

#### Frontend
- **ErrorBoundary** component for graceful error handling
- **Toast notifications** for user feedback (success, error, warning, info)
- **Tooltip system** with financial metric explanations
- **Skeleton loading** components for better perceived performance
- **Custom hooks**:
  - `useAsync` - Async operation handling with loading/error states
  - `useDebounce` - Debounced value updates
  - `useThrottle` - Throttled callback execution
  - `useLocalStorage` - Persistent state with localStorage
  - `useMediaQuery` - Responsive design utilities
  - `useKeyboardShortcut` - Keyboard navigation support
- **Export utilities**:
  - Export to CSV
  - Export to JSON
  - Export portfolio weights
  - Shareable URL generation
- **Accessibility improvements**:
  - ARIA labels and roles
  - Keyboard navigation (Ctrl+R to run, Escape to close)
  - Skip links
  - Focus management
  - Reduced motion support
  - High contrast support
- **Responsive design** for tablet and mobile devices
- **Mobile sidebar** with hamburger menu

#### Documentation
- Comprehensive README with quick start guide
- Architecture documentation with diagrams
- API reference with all endpoints
- Contributing guide
- Changelog

#### Code Quality
- ESLint configuration with TypeScript and accessibility rules
- Prettier configuration for consistent formatting
- Vitest setup for unit testing
- Type-safe development with strict TypeScript

### Changed
- Renamed package to `portfolio-optimizer`
- Bumped version to 2.0.0
- Updated MetricCard to support tooltips and accessibility
- Enhanced StatsTab with export functionality
- Improved main App layout with skip links and mobile support

### Fixed
- TypeScript timer types for browser compatibility (`ReturnType<typeof setTimeout>`)

---

## [1.0.0] - 2026-01-15

### Added
- Initial release of Portfolio Optimizer
- **6 optimization methods**:
  - Maximum Sharpe Ratio
  - Minimum Volatility
  - Minimum CVaR
  - Mean-CVaR Trade-off
  - Maximum Return (Constrained)
  - Exponential Utility (CARA)
- **Portfolio analysis tabs**:
  - Distribution analysis with histograms
  - Allocation visualization (pie/bar charts)
  - Risk analysis with efficient frontier
  - Statistics with comprehensive metrics
- **Interactive sidebar** with:
  - Drag-and-drop file upload
  - Method selection
  - Parameter controls
  - Constraint settings
- **Key metrics display**:
  - Expected Return
  - Volatility
  - Sharpe Ratio
  - CVaR (95%)
  - Max Drawdown
  - Skewness
  - Kurtosis
  - Calmar Ratio
- **Data upload** support for CSV and Excel files
- **FastAPI backend** with async endpoints
- **React frontend** with TypeScript and Tailwind CSS
- **Recharts** visualizations

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 3.0.0 | 2026-02-14 | Flask migration, unified UI (HTMX + Plotly), single Docker service |
| 2.1.0 | 2026-02-07 | Critical fixes, Docker deployment, React frontend, dev tooling |
| 2.0.0 | 2026-01-27 | Enterprise features: A11Y, exports, docs, code quality |
| 1.0.0 | 2026-01-15 | Initial release with 6 optimization methods |

---

## Migration Guides

### Upgrading from 2.x to 3.x

**Breaking Changes:**
- Backend fully rewritten from FastAPI to Flask
- React frontend and Streamlit app removed; replaced by server-rendered Jinja2 + HTMX
- Default port changed from 8000 to 5000
- Docker Compose reduced from 3 services to 1
- uvicorn replaced by gunicorn

**Migration Steps:**
1. Delete `backend/`, `frontend/`, `app.py`, `Dockerfile.streamlit` directories/files
2. The `app/` package is the new Flask application
3. Use `python run.py` (dev) or `gunicorn run:app` (prod) instead of `uvicorn`
4. Update any API client base URLs from port 8000 to 5000
5. API contracts are unchanged — all 7 endpoints at `/api/v1/` return identical JSON

**Configuration:**
- Set `SECRET_KEY` environment variable (required in production)
- `BIND_PORT` replaces `API_PORT` (default 5000)
- `VITE_API_BASE` is no longer needed

---

### Upgrading from 1.x to 2.x

**Breaking Changes:** None - fully backward compatible

**New Dependencies:**
```bash
# Frontend
npm install
# Installs new dev dependencies: eslint, prettier, vitest, etc.

# Backend (no new dependencies)
```

**New Features to Enable:**
1. Wrap your app with `ToastProvider` for notifications
2. Add `ErrorBoundary` for graceful error handling
3. Import hooks from `@/hooks` for custom functionality
4. Use export utilities from `@/utils/export`

**Configuration:**
- ESLint and Prettier configs are pre-configured
- Run `npm run lint` to check code quality
- Run `npm run format` to auto-format code

---

## Links

- [Repository](https://github.com/OWNER/portfolio-optimizer)
- [Documentation](./docs/)
- [Issues](https://github.com/OWNER/portfolio-optimizer/issues)
- [Releases](https://github.com/OWNER/portfolio-optimizer/releases)
